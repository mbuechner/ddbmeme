import errno
import json
import os
import urllib
import requests
from socket import error as SocketError
from django.http import HttpResponsePermanentRedirect
from django.http import JsonResponse
from django.http import StreamingHttpResponse
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.views.generic import CreateView
from ddbmeme.models import Search


class Search(CreateView):
    model = Search
    fields = ('query', 'toptext', 'bottomtext',)

def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

def autocompletemodel(request):
    if not is_ajax(request):
        return

    api_key = os.environ.get('DDB_API_KEY', '')

    # if request.is_ajax():
    query = request.GET.get('query', None)

    data = {
      'got': query
    }

    if (query is None) or not (len(query) == 81) or not query.startswith('https://www.deutsche-digitale-bibliothek.de/item/'):
        data['message'] = '<strong>Example?</strong> Try something like this one: <a id="alert_example" href="#" class="alert-link" style="word-wrap:break-word;">https://www.deutsche-digitale-bibliothek.de/item/CRHMM44XWLG7ZNH55BQ5GSAHTYLXJ7Z4</a>'
        return JsonResponse(data)

    query = query.replace('www.', 'api.')
    query = query.replace('item/', 'items/')

    try:
        response = requests.get(query + '/binaries?oauth_consumer_key=' + api_key)
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise  # Not an error we are looking for
        pass

    if response.status_code != 200:
        data['message'] = '<strong>Ohoh!</strong> I got the error ' + str(response.status_code) + ' from DDB portal. :o('
        return JsonResponse(data)

    j = json.loads(response.text)
    iiif_ulr_prefix = 'https://iiif.deutsche-digitale-bibliothek.de/image/2/'
    iiif_url_suffix = '/full/full/0/default.jpg'

    count = 0

    if j is not None and isinstance(j['binary'], list):
        refs = []
        for e in j['binary']:
            count += 1
            refs.append({
                "uuid": e['@ref'],
                "image": iiif_ulr_prefix + e['@ref'] + iiif_url_suffix,
                })
        data['images'] = json.dumps(refs)
    elif j is not None:
        count += 1
        data['images'] = json.dumps([{
            "uuid": j['binary']['@ref'],
            "image": iiif_ulr_prefix + j['binary']['@ref'] + iiif_url_suffix,
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
        return

    toptext = replacereserved(request.GET.get('toptext', None))
    bottomtext = replacereserved(request.GET.get('bottomtext', None))
    image = request.GET.get('image', None)

    url = "{0}://{1}".format(request.scheme, request.get_host())
    url += HttpResponsePermanentRedirect(reverse('makemememodel')).url
    url += '?alt='
    url += urllib.parse.quote_plus(image)
    url += '&toptext='
    url += urllib.parse.quote_plus(toptext)
    url += '&bottomtext='
    url += urllib.parse.quote_plus(bottomtext)

    data = {
      'url': url,
      'download': url + '&download=true'
    }

    return JsonResponse(data)


def url2yield(url, chunksize=1024):
    try:
        s = requests.Session()
        # Note: here i enabled the streaming
        response = s.get(url, stream=True)

        chunk = True
        while chunk:
            chunk = response.raw.read(chunksize)

            if not chunk:
                break

            yield chunk
    except SocketError as e:
        if e.errno != errno.ECONNRESET:
            raise  # Not an error we are looking for
        pass

def replacereserved(text):
    text = text.replace('-', '--')
    text = text.replace('_', '__')
    text = text.replace(' ', '_')
    text = text.replace('?', '~q')
    text = text.replace('%', '~p')
    text = text.replace('#', '~h')
    text = text.replace('/', '~s')
    text = text.replace('"', '\'\'')
    text = text.replace('', '')
    return text


def makemememodel(request):
    image_url = request.GET.get('alt', 'https://iiif.deutsche-digitale-bibliothek.de/image/2/1dde1d53-07fe-438a-991d-d268b8b1eca7/full/!800,600/0/default.jpg')

    if not image_url.startswith('https://iiif.deutsche-digitale-bibliothek.de/image/'):
        image_url = 'https://iiif.deutsche-digitale-bibliothek.de/image/2/1dde1d53-07fe-438a-991d-d268b8b1eca7/full/!800,600/0/default.jpg'

    toptext = request.GET.get('toptext', '')
    bottomtext = request.GET.get('bottomtext', '')
    download = request.GET.get('download', 'false')

    if len(image_url) <= 0:
        return

    if len(toptext) <= 0 and len(bottomtext) <= 0:
        return

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
