import asyncio
import base64
import shlex
import subprocess
import sys
from http import HTTPMethod
import json
from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import RootModel

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
    lambda: 'https://example.test/search',
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


@pytest.mark.parametrize('debug', [False, True])
def test_content_type_header_rejected(captured_requests, debug):
    @api.post_json(RequestUrl('https://example.test/echo'))
    async def echo():
        return HttpRequest(data={'ping': 1}, extra=HttpRequestExtra(
            headers={'content-type': ContentType.APPLICATION_FORM_URLENCODED}, resp_curl=debug,
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
        return HttpRequest(extra=HttpRequestExtra(resp_curl=True))

    result = asyncio.run(search())
    assert shlex.split(result)[:5] == ['curl', '-g', '-X', 'GET', 'https://example.test/search']
    assert captured_requests == []


def test_http_response_error_status():
    with pytest.raises(httpx.HTTPStatusError):
        HttpResponse(500, 'error', request=httpx.Request('GET', 'https://example.test')).raise_for_status()


def test_curl_get_query_params(captured_requests):
    @api.get(RequestUrl('https://example.test/search?tag=a&tag=b'))
    async def search():
        return HttpRequest(data={'q': 'python'}, extra=HttpRequestExtra(resp_curl=True))

    result = asyncio.run(search())
    assert shlex.split(result)[4] == 'https://example.test/search?tag=a&tag=b&q=python'
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


def _run_curl_stub(command):
    """执行生成命令，但用 shell 函数替代 curl，捕获参数及 stdin，不访问网络。"""
    script = (
        "import base64,json,sys; "
        "print(json.dumps({'args':sys.argv[1:],"
        "'stdin':base64.b64encode(sys.stdin.buffer.read()).decode()}))"
    )
    shell = f'curl() {{ {shlex.quote(sys.executable)} -c {shlex.quote(script)} "$@"; }}\n{command}'
    result = subprocess.run(['/bin/sh', '-c', shell], input=b'', capture_output=True, check=True)
    return json.loads(result.stdout)


@pytest.mark.parametrize('factory,data', [
    (api.post_json, {'name': "O'Reilly", 'value': '中文\n$(printf injected)`printf injected`'}),
    (api.post, {'name': "O'Reilly & 中文", 'tags': ['a', 'b'], 'empty': ''}),
    (api.post_json, {}),
    (api.post_json, None),
    (api.post, {}),
    (api.post, None),
    (api.post_json, '@not-a-file\r\nnext line'),
    (lambda url: api.http(url, HTTPMethod.POST, ContentType.TEXT_PLAIN), '@not-a-file\r\nnext line'),
    (lambda url: api.http(url, HTTPMethod.POST, ContentType.APPLICATION_OCTET_STREAM), b'\x00\xff\r\n\x01'),
    (lambda url: api.http(url, HTTPMethod.POST, ContentType.APPLICATION_OCTET_STREAM), b''),
])
def test_curl_matches_actual_request(factory, data, captured_requests):
    debug = False
    headers = {'X-Token': "O'Reilly $(printf injected)`printf injected`"}

    @factory('https://example.test/items?tag=a&tag=b')
    async def request():
        return HttpRequest(data=data, extra=HttpRequestExtra(headers=headers, resp_curl=debug))

    asyncio.run(request())
    actual = captured_requests[0]
    debug = True
    command = asyncio.run(request())
    assert len(captured_requests) == 1
    assert not command.endswith('\\')
    result = _run_curl_stub(command)
    args = result['args']
    assert args[:4] == ['-g', '-X', actual.method, str(actual.url)]
    assert '-L' not in args
    curl_headers = {}
    for index, arg in enumerate(args):
        if arg == '-H':
            key, value = args[index + 1].split(': ', 1)
            curl_headers[key] = value
    for key, value in curl_headers.items():
        assert actual.headers[key] == value
    if actual.content:
        if '--data-raw' in args:
            payload = args[args.index('--data-raw') + 1].encode()
        else:
            assert args[args.index('--data-binary') + 1] == '@-'
            payload = base64.b64decode(result['stdin'])
        assert payload == actual.content
    else:
        assert '--data-raw' not in args
        assert '--data-binary' not in args
    assert headers == {'X-Token': "O'Reilly $(printf injected)`printf injected`"}


@pytest.mark.parametrize('method', [HTTPMethod.GET, HTTPMethod.HEAD, HTTPMethod.OPTIONS])
def test_curl_query_methods(method, captured_requests):
    @api.http('https://example.test/search?tag=a&tag=b', method)
    async def request():
        return HttpRequest(
            data={'q': "O'Reilly & 中文", 'filter[]': ['a', 'b']},
            extra=HttpRequestExtra(resp_curl=True),
        )

    result = _run_curl_stub(asyncio.run(request()))
    args = result['args']
    assert args[:3] == ['-g', '-X', str(method)]
    assert ('--head' in args) == (method == HTTPMethod.HEAD)
    params = httpx.URL(args[3]).params
    assert params.get_list('tag') == ['a', 'b']
    assert params['q'] == "O'Reilly & 中文"
    assert params.get_list('filter[]') == ['a', 'b']
    assert '--data-raw' not in args
    assert captured_requests == []


def test_curl_skips_business_response_processing(captured_requests):
    success = Mock(side_effect=AssertionError('must not check a debug response'))
    parser = Mock(side_effect=AssertionError('must not parse a debug response'))

    @api.post_json('https://example.test/echo', success=success, parser=parser)
    async def request():
        return HttpRequest(data={}, extra=HttpRequestExtra(
            resp_curl=True, resp_json=True, resp_model=RootModel[int],
        ))

    assert _run_curl_stub(asyncio.run(request()))['args'][2] == 'POST'
    success.assert_not_called()
    parser.assert_not_called()
    assert captured_requests == []
