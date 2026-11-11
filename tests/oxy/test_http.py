import asyncio
import json
import unittest
from unittest.mock import AsyncMock, patch

import httpx

from oxy.utils.http import api, make_response_processors, HttpResponse
from oxy.utils.http.http_response_model import HEADERS_PARAMS


@api.get('https://example.test/search')
async def example_search():
    return {'q': 'python'}


@api.post_json(lambda: 'https://example.test/echo', **make_response_processors(
    success=lambda resp: resp.get('ok') is True,
    error_msg=lambda resp: resp.get('error', 'fail'),
    parser=lambda resp, _: resp['data'],
))
async def example_echo(*, token: str):
    return {
        HEADERS_PARAMS: {'Authorization': token},
        'ping': 1,
    }


class HttpTestCase(unittest.TestCase):
    def test_http_response_properties(self):
        resp = HttpResponse(200, 'curl ...')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.text, 'curl ...')
        resp.raise_for_status()
        with self.assertRaises(json.JSONDecodeError):
            resp.json()

    def test_get_with_mock(self):
        mock_response = httpx.Response(
            200,
            json={'ok': True},
            request=httpx.Request('GET', 'https://example.test/search'),
        )

        async def _run():
            with patch('oxy.utils.http.api._do_get', new_callable=AsyncMock) as mocked:
                mocked.return_value = mock_response
                result = await example_search()
                mocked.assert_awaited()
                self.assertEqual(result, {'ok': True})

        asyncio.run(_run())

    def test_post_json_lazy_url_and_parser(self):
        mock_response = httpx.Response(
            200,
            json={'ok': True, 'data': {'pong': 1}},
            request=httpx.Request('POST', 'https://example.test/echo'),
        )

        async def _run():
            with patch('oxy.utils.http.api._do_post_json', new_callable=AsyncMock) as mocked:
                mocked.return_value = mock_response
                result = await example_echo(token='tok')
                self.assertEqual(result, {'pong': 1})
                args = mocked.await_args.args
                self.assertEqual(args[0], 'https://example.test/echo')
                self.assertEqual(args[2].get('Authorization'), 'tok')

        asyncio.run(_run())


if __name__ == '__main__':
    unittest.main()
