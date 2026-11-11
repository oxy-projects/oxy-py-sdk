import asyncio
import json
from unittest.mock import patch

import httpx
import pytest

from oxy.utils.http import api, ContentType, HttpRequest, HttpRequestExtra, HttpResponse
from oxy.utils.http._model import RequestUrl


@pytest.fixture
def captured_requests():
    requests = []
    real_client = httpx.AsyncClient

    def handler(request):
        requests.append(request)
        return httpx.Response(200, json={'ok': True, 'data': {'pong': 1}})

    with patch('oxy.utils.http._api.AsyncClient',
               side_effect=lambda **kwargs: real_client(
                   transport=httpx.MockTransport(handler), **kwargs)):
        yield requests


@pytest.mark.parametrize('url', [
    'https://example.test/search',
    RequestUrl('https://example.test/search'),
    lambda: RequestUrl('https://example.test/search'),
])
def test_get(url, captured_requests):
    @api.get(url)
    async def search():
        return {'q': 'python'}

    assert asyncio.run(search())['ok'] is True
    assert str(captured_requests[0].url) == 'https://example.test/search?q=python'


def test_post_json_headers_and_parser(captured_requests):
    @api.post_json(
        RequestUrl('https://example.test/echo'),
        success=lambda response: response['ok'],
        parser=lambda response, context: {**response['data'], **context},
    )
    async def echo(*, token):
        return HttpRequest(
            data={'ping': 1},
            extra=HttpRequestExtra(
                headers={'Authorization': token}, context={'source': 'test'},
            ),
        )

    assert asyncio.run(echo(token='tok')) == {'pong': 1, 'source': 'test'}
    request = captured_requests[0]
    assert request.method == 'POST'
    assert request.headers['Authorization'] == 'tok'
    assert request.headers['Content-Type'] == 'application/json'
    assert json.loads(request.content) == {'ping': 1}


def test_content_type_header_rejected(captured_requests):
    @api.post_json(RequestUrl('https://example.test/echo'))
    async def echo():
        return HttpRequest(data={'ping': 1}, extra=HttpRequestExtra(
            headers={'content-type': ContentType.APPLICATION_FORM_URLENCODED},
        ))

    with pytest.raises(ValueError, match='headers'):
        asyncio.run(echo())
    assert captured_requests == []


def test_http_response_properties():
    response = HttpResponse(200, 'curl ...', request=httpx.Request('GET', 'https://example.test'))
    assert response.status_code == 200
    assert response.text == 'curl ...'
    assert response.raise_for_status() is response
    with pytest.raises(json.JSONDecodeError):
        response.json()


@pytest.mark.parametrize('data', [None, {}, {'q': 'python', 'page': 2}])
def test_get_preserves_url_query(data, captured_requests):
    @api.get('https://example.test/search?token=abc&tag=a&tag=b&page=1')
    async def search():
        return data

    asyncio.run(search())
    params = captured_requests[0].url.params
    assert params['token'] == 'abc'
    assert params.get_list('tag') == ['a', 'b']
    assert params['page'] == ('2' if data else '1')
    if data:
        assert params['q'] == 'python'


def test_reusing_request_headers(captured_requests):
    extra = HttpRequestExtra(headers={'Authorization': 'tok'})

    @api.post_json('https://example.test/echo')
    async def echo():
        return HttpRequest(data={'ping': 1}, extra=extra)

    async def run():
        await echo()
        await echo()

    asyncio.run(run())
    assert extra.headers == {'Authorization': 'tok'}
    assert len(captured_requests) == 2
    for request in captured_requests:
        assert request.headers['Content-Type'] == 'application/json'


def test_curl_debug_does_not_send_request(captured_requests):
    @api.get('https://example.test/search')
    async def search():
        return HttpRequest(extra=HttpRequestExtra(is_resp_curl=True))

    result = asyncio.run(search())
    assert result.startswith("curl -L -X GET 'https://example.test/search'")
    assert captured_requests == []


def test_http_response_error_status():
    with pytest.raises(httpx.HTTPStatusError):
        HttpResponse(500, 'error', request=httpx.Request('GET', 'https://example.test')).raise_for_status()


def test_curl_get_query_params(captured_requests):
    @api.get(RequestUrl('https://example.test/search?tag=a&tag=b'))
    async def search():
        return HttpRequest(data={'q': 'python'}, extra=HttpRequestExtra(is_resp_curl=True))

    result = asyncio.run(search())
    assert "'https://example.test/search?tag=a&tag=b&q=python'" in result
    assert '\n-d ' not in result
    assert captured_requests == []


@pytest.mark.parametrize('url', [
    RequestUrl('https://example.test/users/{uid}'),
    RequestUrl('https://example.test', path='/users/{uid}'),
])
def test_path_template_reused(url, captured_requests):
    @api.get(url)
    async def user(*, uid):
        return None

    async def run():
        await user(uid=1)
        await user(uid=2)

    asyncio.run(run())
    assert [request.url.path for request in captured_requests] == ['/users/1', '/users/2']


def test_post_extra_query_params(captured_requests):
    @api.post_json(RequestUrl('https://example.test/items?tag=a&tag=b'))
    async def items():
        return HttpRequest(data={}, extra=HttpRequestExtra(
            query_params=httpx.QueryParams({'token': 'abc'}),
        ))

    asyncio.run(items())
    params = captured_requests[0].url.params
    assert params['token'] == 'abc'
    assert params.get_list('tag') == ['a', 'b']
