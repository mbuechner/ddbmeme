import json
import logging
import re
from threading import BoundedSemaphore, local
from urllib.parse import quote, urlencode, urlsplit

import requests
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.decorators.http import require_GET, require_safe
from requests.adapters import HTTPAdapter

logger = logging.getLogger(__name__)

DDB_HOST = 'www.deutsche-digitale-bibliothek.de'
DDB_API = 'https://api.deutsche-digitale-bibliothek.de/2/items'
IIIF_HOST = 'iiif.deutsche-digitale-bibliothek.de'
DEFAULT_IMAGE_URL = (
    f'https://{IIIF_HOST}/image/2/5df8523e-7ee1-4aa6-b690-cb2c7580f13c/full/!800,600/0/default.jpg'
)
MAX_CAPTION_BYTES = 200

CAPTION_ESCAPES = str.maketrans({
    '_': '__',
    ' ': '_',
    '-': '--',
    '?': '~q',
    '&': '~a',
    '%': '~p',
    '#': '~h',
    '/': '~s',
    '\\': '~b',
    '\n': '~n',
    '<': '~l',
    '>': '~g',
    '"': "''",
})

_memegen_semaphore = BoundedSemaphore(settings.MEMEGEN_MAX_CONCURRENCY)
_thread = local()


def get_memegen_session():
    # Each Gunicorn thread reuses its own connections and session state.
    if not hasattr(_thread, 'memegen_session'):
        session = requests.Session()
        adapter = HTTPAdapter(max_retries=settings.MEMEGEN_RETRY_TOTAL)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        _thread.memegen_session = session
    return _thread.memegen_session


@require_safe
def health(request):
    return HttpResponse('ok', content_type='text/plain')


def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'


def get_ddb_item_id(url):
    try:
        parsed = urlsplit(url.strip())
    except ValueError:
        return None
    if parsed.scheme == 'https' and parsed.netloc == DDB_HOST:
        match = re.fullmatch(r'/item/([A-Z0-9]{32})/?', parsed.path, re.IGNORECASE | re.ASCII)
        if match:
            return match[1].upper()
    return None


def make_iiif_url(reference):
    return f'https://{IIIF_HOST}/image/2/{quote(reference, safe="")}/full/!800,600/0/default.jpg'


@require_GET
def autocompletemodel(request):
    if not is_ajax(request):
        return HttpResponseBadRequest('Only AJAX requests are allowed')

    query = request.GET.get('query', '')
    data = {'got': query}
    item_id = get_ddb_item_id(query)
    if item_id is None:
        return JsonResponse({**data, 'message': 'Try this DDB object as an example.', 'show_example': True})

    try:
        response = requests.get(
            f'{DDB_API}/{item_id}/binaries',
            headers={'Accept': 'application/json'},
            timeout=10,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        logger.warning('DDB image lookup failed for %s: %s', item_id, exc)
        return JsonResponse({**data, 'message': 'The DDB portal could not be reached. Please try again.'})

    if response.status_code != 200:
        logger.warning('DDB image lookup returned HTTP %s for %s', response.status_code, item_id)
        return JsonResponse({**data, 'message': f'The DDB portal returned HTTP {response.status_code}.'})

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError:
        return JsonResponse({**data, 'message': 'The DDB portal returned an invalid response.'})

    binaries = payload.get('binary') if isinstance(payload, dict) else None
    if isinstance(binaries, dict):
        binaries = [binaries]
    images = []
    seen = set()
    for binary in binaries if isinstance(binaries, list) else ():
        reference = binary.get('ref') if isinstance(binary, dict) else None
        if isinstance(reference, str) and reference and reference not in seen:
            images.append({'uuid': reference, 'image': make_iiif_url(reference)})
            seen.add(reference)

    if images:
        count = len(images)
        data['message'] = '1 picture found.' if count == 1 else f'{count} pictures found.'
        # Preserve the existing JSON-encoded images field for clients.
        data['images'] = json.dumps(images)
    else:
        data['message'] = "This DDB object doesn't contain any pictures."
    return JsonResponse(data)


def replacereserved(text):
    return text.translate(CAPTION_ESCAPES)


def caption_error(toptext, bottomtext):
    if not toptext.strip() and not bottomtext.strip():
        return 'Top text or bottom text is required'
    if max(len(toptext.encode('utf-8')), len(bottomtext.encode('utf-8'))) > MAX_CAPTION_BYTES:
        return 'A caption is too long after encoding. Please shorten it.'
    return None


@require_GET
def maketextmodel(request):
    if not is_ajax(request):
        return HttpResponseBadRequest('Only AJAX requests are allowed')

    toptext = request.GET.get('toptext', '')
    bottomtext = request.GET.get('bottomtext', '')
    top = replacereserved(toptext) if toptext.strip() else ''
    bottom = replacereserved(bottomtext) if bottomtext.strip() else ''
    if error := caption_error(top, bottom):
        return JsonResponse({'message': error}, status=400)

    base_url = request.build_absolute_uri(reverse('makemememodel'))
    query = urlencode({'alt': request.GET.get('image', ''), 'toptext': top, 'bottomtext': bottom})
    url = f'{base_url}?{query}'
    return JsonResponse({'url': url, 'download': f'{url}&download=true'})


def get_background_url(url):
    try:
        parsed = urlsplit(url)
    except ValueError:
        return DEFAULT_IMAGE_URL
    if parsed.scheme == 'https' and parsed.netloc == IIIF_HOST and parsed.path.startswith('/image/'):
        return url
    return DEFAULT_IMAGE_URL


@require_safe
def makemememodel(request):
    toptext = request.GET.get('toptext', '')
    bottomtext = request.GET.get('bottomtext', '')
    if error := caption_error(toptext, bottomtext):
        return HttpResponseBadRequest(error)

    image_url = get_background_url(request.GET.get('alt', ''))
    # Preserve literal dots when the first caption would otherwise be a URL dot segment.
    top_segment = f'{toptext}_' if toptext in ('.', '..') else toptext
    top = quote(top_segment or '_', safe='')
    bottom = quote(bottomtext or '_', safe='')
    base = settings.MEMEGEN_BASE_URL.rstrip('/')
    url = f'{base}/images/custom/{top}/{bottom}.jpg'

    if not _memegen_semaphore.acquire(timeout=settings.MEMEGEN_QUEUE_WAIT_SECONDS):
        logger.warning('Memegen busy: concurrency limit reached')
        return HttpResponse('Image service is busy, please retry in a moment', status=503)

    try:
        result = get_memegen_session().get(
            url, params={'background': image_url}, timeout=settings.MEMEGEN_TIMEOUT,
        )
        result.raise_for_status()
        media_type = result.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
        if media_type != 'image/jpeg' or not result.content:
            logger.warning('Memegen returned a response without a JPEG image')
            return HttpResponse('Image generation failed', status=502)

        response = HttpResponse(result.content, content_type='image/jpeg')
        if request.GET.get('download') == 'true':
            filename = slugify(f'{toptext}_{bottomtext}')
            response['Content-Disposition'] = f'attachment; filename="DDBmeme-{filename}.jpg"'
        return response
    except requests.Timeout:
        logger.warning('Memegen timed out while generating an image')
        return HttpResponse('Image generation timed out', status=504)
    except requests.RequestException as exc:
        logger.warning('Memegen request failed (%s)', type(exc).__name__)
        return HttpResponse('Image generation failed', status=502)
    finally:
        _memegen_semaphore.release()
