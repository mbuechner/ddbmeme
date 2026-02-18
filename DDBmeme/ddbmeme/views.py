import errno
import json
import urllib.parse
import logging
import requests
import urllib3.exceptions

# logging is configured centrally in settings.py; use module logger
from socket import error as SocketError
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.generic import CreateView
from django.http import HttpResponseBadRequest
from ddbmeme.models import Search as SearchModel

class Search(CreateView):
    model = SearchModel
    fields = ('query', 'toptext', 'bottomtext',)

def is_ajax(request):
    return request.headers.get('X-Requested-With') == 'XMLHttpRequest'

def autocompletemodel(request):
    if not is_ajax(request):
        return HttpResponseBadRequest("Only AJAX requests are allowed")

    query = request.GET.get('query', None)

    data = {
      'got': query
    }

    if (query is None) or not (len(query) == 81) or not query.startswith('https://www.deutsche-digitale-bibliothek.de/item/'):
        data['message'] = '<strong>Example?</strong> Try something like this one: <a id="alert_example" href="#" class="alert-link" style="word-wrap:break-word;">https://www.deutsche-digitale-bibliothek.de/item/AVSHSWYGR4NBLVXV4IOZRN2PO2KFOEVF</a>'
        return JsonResponse(data)

    query = query.replace('/www.', '/api.')
    query = query.replace('/item/', '/2/items/')

    response = None
    error_message = None

    try:
        response = requests.get(query + '/binaries', headers={'Accept': 'application/json'}, timeout=10)
    except requests.RequestException as e:
        error_message = f"Request failed: {str(e)}"
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"

    if response is None or response.status_code != 200:
        error_code = response.status_code if response is not None else 'unknown'
        if error_message:
            data['message'] = f'<strong>Ohoh!</strong> {error_message}'
        else:
            data['message'] = f'<strong>Ohoh!</strong> I got the error {error_code} from DDB portal. :o('
        return JsonResponse(data)

    try:
        j = json.loads(response.text)
    except json.JSONDecodeError:
        data['message'] = '<strong>Ohoh!</strong> Invalid response from DDB portal.'
        return JsonResponse(data)
    iiif_ulr_prefix = 'https://iiif.deutsche-digitale-bibliothek.de/image/2/'
    iiif_url_suffix = '/full/!800,600/0/default.jpg'

    count = 0

    if j is not None and isinstance(j['binary'], list):
        refs = []
        for e in j['binary']:
            count += 1
            refs.append({
                "uuid": e['ref'],
                "image": iiif_ulr_prefix + e['ref'] + iiif_url_suffix,
                })
        data['images'] = json.dumps(refs)
    elif j is not None:
        count += 1
        data['images'] = json.dumps([{
            "uuid": j['binary']['ref'],
            "image": iiif_ulr_prefix + j['binary']['ref'] + iiif_url_suffix,
            }])
    if count == 0:
        data['message'] = 'This DDB object doesn\'t contain any pictures.'
    elif count == 1:
        data['message'] = str(count) + ' picture found.'
    else:
        data['message'] = str(count) + ' pictures found.'

    return JsonResponse(data)

def maketextmodel(request):
    if not is_ajax(request):
        return HttpResponseBadRequest("Only AJAX requests are allowed")

    toptext = replacereserved(request.GET.get('toptext', None))
    bottomtext = replacereserved(request.GET.get('bottomtext', None))
    image = request.GET.get('image', None)

    base_url = request.build_absolute_uri(reverse('makemememodel'))
    params = {
        'alt': image,
        'toptext': toptext,
        'bottomtext': bottomtext,
    }
    query_string = urllib.parse.urlencode(params)
    url = f"{base_url}?{query_string}"

    data = {
        'url': url,
        'download': f"{url}&download=true"
    }

    return JsonResponse(data)

def url2yield(url, chunksize=1024):
    logger = logging.getLogger(__name__)
    try:
        s = requests.Session()
        # enable streaming with a timeout to avoid hanging indefinitely
        response = s.get(url, stream=True, timeout=10)
        response.raise_for_status()

        for chunk in response.iter_content(chunk_size=chunksize):
            if not chunk:
                break
            yield chunk
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise
        logger.error("Socket connection reset while streaming %s: %s", url, e)
    except (requests.RequestException, urllib3.exceptions.ProtocolError) as e:
        logger.error("HTTP streaming failed for %s: %s", url, e)
    except Exception as e:
        logger.exception("Unexpected error while streaming %s: %s", url, e)

def replacereserved(text):
    text = text.replace(' ', '_')
    text = text.replace('_', '__')
    text = text.replace('-', '--')
    text = text.replace('?', '~q')
    text = text.replace('&', '~a')
    text = text.replace('%', '~p')
    text = text.replace('#', '~h')
    text = text.replace('/', '~s')
    text = text.replace('\\', '~b')
    text = text.replace('<', '~l')
    text = text.replace('>', '~g')
    text = text.replace('"', '\'\'')
    return text

def makemememodel(request):
    image_url = request.GET.get('alt', 'https://iiif.deutsche-digitale-bibliothek.de/image/2/5df8523e-7ee1-4aa6-b690-cb2c7580f13c/full/!800,600/0/default.jpg')

    if not image_url.startswith('https://iiif.deutsche-digitale-bibliothek.de/image/'):
        image_url = 'https://iiif.deutsche-digitale-bibliothek.de/image/2/5df8523e-7ee1-4aa6-b690-cb2c7580f13c/full/!800,600/0/default.jpg'

    toptext = request.GET.get('toptext', '')
    bottomtext = request.GET.get('bottomtext', '')
    download = request.GET.get('download', 'false')

    if len(image_url) <= 0:
        return HttpResponseBadRequest("Invalid image URL")

    if len(toptext) <= 0 and len(bottomtext) <= 0:
        return HttpResponseBadRequest("Top text or bottom text is required")

    # service could running locally under port 5001
    url = 'http://localhost:5001/images/custom/'
    if len(toptext) > 0:
        url += urllib.parse.quote_plus(toptext) + '/'
    else:
        url += '_/'
    if len(bottomtext) > 0:
        url += urllib.parse.quote_plus(bottomtext) + '/'
    url = url[:-1] + '.jpg?background=' + urllib.parse.quote_plus(image_url)

    response = StreamingHttpResponse(url2yield(url), content_type="image/jpeg")

    if download == 'true':
        response['Content-Disposition'] = 'attachment; filename="DDBmeme-' + slugify(toptext + '_' + bottomtext) + '.jpg"'

    return response
