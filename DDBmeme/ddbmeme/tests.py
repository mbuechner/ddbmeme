import json
from unittest.mock import Mock, patch
from urllib.parse import parse_qs, urlsplit

import requests
from django.test import SimpleTestCase
from django.urls import reverse

from ddbmeme import views


AJAX_HEADERS = {'X-Requested-With': 'XMLHttpRequest'}
DDB_ITEM = 'CRHMM44XWLG7ZNH55BQ5GSAHTYLXJ7Z4'
DDB_URL = f'https://{views.DDB_HOST}/item/{DDB_ITEM}'


class SearchTests(SimpleTestCase):
    def test_home_page_get_and_post(self):
        url = reverse('search_base')
        self.assertContains(self.client.get(url), 'DDBmeme')
        self.assertEqual(self.client.post(url).status_code, 405)

    @patch('ddbmeme.views.requests.get')
    def test_invalid_item_url_does_not_call_the_api(self, get):
        response = self.client.get(
            reverse('autocompletemodel'), {'query': 'https://example.org/item/' + DDB_ITEM},
            headers=AJAX_HEADERS,
        )
        self.assertTrue(response.json()['show_example'])
        get.assert_not_called()

    @patch('ddbmeme.views.requests.get')
    def test_lookup_accepts_copied_url_and_deduplicates_binary_references(self, get):
        get.return_value = Mock(status_code=200)
        get.return_value.json.return_value = {
            'binary': [{'ref': 'a'}, {'description': 'No reference'}, {'ref': 'a'}, {'ref': 'b'}],
        }
        response = self.client.get(
            reverse('autocompletemodel'), {'query': f' {DDB_URL}/?query=example#details '},
            headers=AJAX_HEADERS,
        )
        self.assertEqual(get.call_args.args[0], f'{views.DDB_API}/{DDB_ITEM}/binaries')
        self.assertEqual([item['uuid'] for item in json.loads(response.json()['images'])], ['a', 'b'])

    @patch('ddbmeme.views.requests.get')
    def test_single_binary_dictionary_and_empty_result(self, get):
        get.return_value = Mock(status_code=200)
        for payload, expected in (
            ({'binary': {'ref': 'a'}}, '1 picture found.'),
            ({}, "This DDB object doesn't contain any pictures."),
            ({'binary': None}, "This DDB object doesn't contain any pictures."),
        ):
            with self.subTest(payload=payload):
                get.return_value.json.return_value = payload
                response = self.client.get(
                    reverse('autocompletemodel'), {'query': DDB_URL}, headers=AJAX_HEADERS,
                )
                self.assertEqual(response.json()['message'], expected)


class MemeTests(SimpleTestCase):
    def test_meme_links_work_with_a_single_caption(self):
        response = self.client.get(
            reverse('maketextmodel'), {'toptext': 'A & B', 'image': views.DEFAULT_IMAGE_URL},
            headers=AJAX_HEADERS,
        )
        data = response.json()
        self.assertEqual(parse_qs(urlsplit(data['url']).query)['toptext'], ['A_~a_B'])
        self.assertEqual(parse_qs(urlsplit(data['download']).query)['download'], ['true'])

    def test_missing_and_oversized_captions_are_rejected(self):
        for captions in ({}, {'bottomtext': '🐕' * 51}):
            with self.subTest(captions=captions):
                response = self.client.get(reverse('maketextmodel'), captions, headers=AJAX_HEADERS)
                self.assertEqual(response.status_code, 400)
                self.assertIn('message', response.json())

    @patch('ddbmeme.views.get_memegen_session')
    def test_meme_paths_encode_spaces_and_preserve_downloads(self, session):
        get = session.return_value.get
        get.return_value = Mock(headers={'Content-Type': 'image/jpeg'}, content=b'jpeg')
        response = self.client.get(
            reverse('makemememodel'),
            {'alt': 'https://example.org/outside-ddb', 'toptext': 'A B', 'download': 'true'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b'jpeg')
        self.assertIn('attachment;', response.headers['Content-Disposition'])
        self.assertTrue(get.call_args.args[0].endswith('/images/custom/A%20B/_.jpg'))
        self.assertEqual(get.call_args.kwargs['params'], {'background': views.DEFAULT_IMAGE_URL})

    @patch('ddbmeme.views.get_memegen_session')
    def test_timeout_releases_the_generation_slot(self, session):
        get = session.return_value.get
        get.side_effect = [requests.Timeout(), Mock(headers={'Content-Type': 'image/jpeg'}, content=b'jpeg')]
        url = reverse('makemememodel')
        with patch.object(views, '_memegen_semaphore', views.BoundedSemaphore(1)):
            with self.assertLogs('ddbmeme.views', level='WARNING'):
                self.assertEqual(self.client.get(url, {'toptext': 'Example'}).status_code, 504)
            self.assertEqual(self.client.get(url, {'toptext': 'Example'}).status_code, 200)

    @patch('ddbmeme.views.get_memegen_session')
    def test_upstream_non_image_is_reported_as_a_gateway_error(self, session):
        session.return_value.get.return_value = Mock(headers={'Content-Type': 'text/html'}, content=b'html')
        with self.assertLogs('ddbmeme.views', level='WARNING'):
            response = self.client.get(reverse('makemememodel'), {'toptext': 'Example'})
        self.assertEqual(response.status_code, 502)
