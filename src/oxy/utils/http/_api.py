import json
from dataclasses import dataclass
from functools import wraps, cached_property
from http import HTTPMethod
from json import JSONDecodeError
from typing import Any, Optional, Callable, Mapping

from httpx import Response, HTTPStatusError, Request, AsyncClient, QueryParams
from pydantic import BaseModel

from oxy.utils.http._model import (
    ContentType, ContentTypeName, HttpUrl, HttpResponse, HttpRequestExtra,
    HttpRequest, RequestUrl, HttpContext, HttpLogs,
)
from oxy.utils.lang import logger
from oxy.utils.lang.charset import Charset

_log = logger.of(__name__)


def _default_success(response) -> bool:
    return True


def _default_error_msg(response) -> Optional[str]:
    if not response:
        return ''
    if isinstance(response, str):
        return response
    if isinstance(response, Mapping):
        return response.get('message', None) or response.get('msg', None) or str(response)
    return str(response)


def _default_response_parser(response, context: HttpContext) -> Any:
    return response


@dataclass(frozen=True)
class ParsedRequest:
    url: HttpUrl
    headers: dict[str, Any]
    context: HttpContext
    req_data: str | bytes | dict[str, Any] | QueryParams | None = None
    resp_model: type[BaseModel] | None = None
    is_resp_json: bool = False
    is_resp_curl: bool = False

    @cached_property
    def full_path(self):
        return str(self.url.url)


def only_http_with_query_params(method: HTTPMethod):
    return method in [
        HTTPMethod.GET,
        HTTPMethod.OPTIONS,
        HTTPMethod.HEAD,
    ]


async def _common_request_parser(
    url: RequestUrl,
    method: HTTPMethod,
    func,
    *args, **kwargs
) -> ParsedRequest:
    # 使用参数前，提前校验python语法规定
    _func_return = await func(*args, **kwargs)

    # 解析：请求参数、扩展参数
    req_data, extra_data = (
        (_func_return.data, _func_return.extra)
        if isinstance(_func_return, HttpRequest)
        else (_func_return, None)
    )

    # 扩展参数加工
    extra_data = extra_data or HttpRequestExtra()
    assert isinstance(extra_data, HttpRequestExtra), "扩展参数必须为Extra类型"

    # 请求参数加工
    if isinstance(req_data, str):
        try:
            req_data = json.loads(req_data)
        except JSONDecodeError as e:
            # 原值为准
            pass

    # 对URL的PATH占位符进行格式化
    _url = url.copy_with(query_params=extra_data.query_params).format_url_path(**kwargs)
    if only_http_with_query_params(method):
        req_data = _url.url.params.merge(req_data or {})

    return ParsedRequest(
        url=_url,
        headers=extra_data.headers,
        context=extra_data.context,
        req_data=req_data,
        resp_model=extra_data.resp_model,
        is_resp_json=extra_data.is_resp_json,
        is_resp_curl=extra_data.is_resp_curl,
    )


def _common_response_parser(
    http_response: Response,
    context: HttpContext,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    resp_parser: Callable[[Any, Any], Any] = _default_response_parser,
    model: type[BaseModel] | None = None,
) -> Any:
    # 非2xx状态校验
    http_response.raise_for_status()
    # 转JSON
    try:
        response = http_response.json()
    except JSONDecodeError as e:
        response = http_response.text
    if success(response):
        return _to_model(resp_parser(response, context), model)
    else:
        raise HTTPStatusError(f'🐞 {error_msg(response)}', request=http_response.request, response=http_response)


def _to_model(json_data: str | dict | list[dict], model: type[BaseModel] | None):
    if model is None:
        return json_data
    if isinstance(json_data, str):
        return model.model_validate_json(json_data)
    if isinstance(json_data, dict | list):
        return model.model_validate(json_data)
    raise TypeError(f"当前类型不支持转 model：{type(json_data).__name__}")


def _do_print_curl(
    url: str,
    method: HTTPMethod,
    req_data: str | bytes | dict[str, Any] | QueryParams | None,
    headers,
) -> Response:
    if only_http_with_query_params(method):
        assert isinstance(req_data, QueryParams)
        url = str(HttpUrl(url, query_params=req_data).url)
        req_data = None
    headers_str = ''
    if headers is not None and len(headers) > 0:
        for _k, _v in headers.items():
            headers_str += f"\n-H '{_k}: {_v}' \\"
    req_data_str = ''
    if req_data is not None:
        req_data_str = '\n-d '
        if isinstance(req_data, str):
            req_data_str += f"'{req_data}'"
        elif isinstance(req_data, dict):
            req_data_str += f"'{json.dumps(req_data, ensure_ascii=False, indent=2)}'"
        else:
            raise ValueError("CURL格式化req_data暂时只支持`str`和`dict`")
    curl_resp_content = f"curl -L -X {str(method)} '{url}' \\{headers_str}{req_data_str}"
    return HttpResponse(200, curl_resp_content, request=Request(method, url))


async def _do_http(
    url: str,
    method: HTTPMethod = HTTPMethod.GET,
    content_type: ContentType = ContentType.ALL,
    charset: Charset = Charset.UTF_8,
    req_data: str | bytes | dict[str, Any] | QueryParams | None = None,
    headers: dict[str, Any] | None = None,
) -> Response:
    headers = dict(headers) if headers is not None else {}
    async with AsyncClient(http2=True) as client:
        # 优先校验请求头参数
        _req_content_types = {
            k: v for k, v in headers.items() if k.lower() == ContentTypeName.lower()
        }
        if _req_content_types:
            raise ValueError(f"请不要在`headers`中设置`{ContentTypeName}`，而应该设置在`content_type`")
        # 其次取方法参数
        _content_type = (content_type if content_type != ContentType.ALL else None)

        # 请求类型
        is_only_query_params = only_http_with_query_params(method)
        if req_data is not None and not is_only_query_params:
            if not _content_type :
                raise ValueError("请输入`HTTP`的`Content-Type`")
            headers[ContentTypeName] = _content_type.with_charset(charset)
        # 请求体类型
        is_form_kv: bool = (content_type == ContentType.APPLICATION_FORM_URLENCODED)
        is_json: bool = (content_type == ContentType.APPLICATION_JSON)

        # 区分请求方法参数调用
        _params = None
        _form_kv_data = None
        _json_data = None
        _content_data: str | bytes | None = None
        if is_only_query_params:
            assert req_data is None or isinstance(req_data, (dict, QueryParams))
            _params = req_data
        else:
            if is_form_kv:
                assert req_data is None or isinstance(req_data, dict)
                _form_kv_data = req_data
            elif is_json:
                if isinstance(req_data, str):
                    _content_data = req_data
                else:
                    assert req_data is None or isinstance(req_data, dict)
                    _json_data = req_data
            else:
                assert not isinstance(req_data, QueryParams)
                _content_data = (
                    json.dumps(req_data)
                    if isinstance(req_data, dict)
                    else req_data
                )
        return await client.request(
            method=method,
            url=url,
            params=_params,
            data=_form_kv_data,
            json=_json_data,
            content=_content_data,
            headers=headers,
        )


def _http(
    url: str | RequestUrl | Callable[[], RequestUrl],
    method: HTTPMethod = HTTPMethod.GET,
    content_type: ContentType = ContentType.ALL,
    charset: Charset = Charset.UTF_8,
    *,
    success: Callable[[Any], bool],
    error_msg: Callable[[Any], Optional[str]],
    resp_parser: Callable[[Any, HttpContext], Any],
    log: HttpLogs = HttpLogs.DEFAULT,
) -> Callable[[Any], Any]:
    """
    HTTP 请求
    :param url: 地址，或返回地址的 callable（惰性解析，便于配置后加载）
    :param success: 判断响应成功：(resp) => bool
    :param error_msg: 获取响应失败信息：(resp) => str
    :param resp_parser: 获取响应有效数据：(resp, context) => resp
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            nonlocal url
            nonlocal log

            _resolved_url = url() if callable(url) else url
            _resolved_url = RequestUrl(_resolved_url) if isinstance(_resolved_url, str) else _resolved_url
            assert isinstance(_resolved_url, RequestUrl), "请输入正确的`RequestUrl`"

            parsed_request: ParsedRequest = await _common_request_parser(
                _resolved_url, method, func, *args, **kwargs
            )
            try:
                req_data_log = json.dumps(parsed_request.req_data, ensure_ascii=False)
            except (JSONDecodeError, TypeError):
                req_data_log = parsed_request.req_data
            try:
                if log.req:
                    _log.debug(
                        'API请求开始，url=%s，request=%s',
                        parsed_request.full_path, req_data_log
                    )
                resp_data = _common_response_parser(
                    http_response=(
                        _do_print_curl(
                            url=str(parsed_request.full_path),
                            method=method,
                            req_data=parsed_request.req_data,
                            headers=parsed_request.headers,
                        )
                        if parsed_request.is_resp_curl else
                        await _do_http(
                            url=str(parsed_request.full_path),
                            method=method,
                            content_type=content_type,
                            charset=charset,
                            req_data=parsed_request.req_data,
                            headers=parsed_request.headers,
                        )
                    ),
                    context=parsed_request.context,
                    success=success,
                    error_msg=error_msg,
                    resp_parser=resp_parser,
                    model=parsed_request.resp_model,
                )
                if log.resp:
                    try:
                        resp_data_log = json.dumps(resp_data, ensure_ascii=False)
                    except (JSONDecodeError, TypeError):
                        resp_data_log = resp_data
                    _log.debug(
                        'API请求成功，url=%s，request=%s，response=%s',
                        parsed_request.full_path, req_data_log, resp_data_log
                    )
                return (
                    resp_data
                    if isinstance(resp_data, str) or not parsed_request.is_resp_json else
                    json.dumps(resp_data, ensure_ascii=False)
                )
            except HTTPStatusError as err:
                _log.error(
                    'API请求失败，url=%s，request=%s，http_status=%s，response=%s',
                    parsed_request.full_path, req_data_log, err.response.status_code, err.response.text
                )
                raise err
        return wrapper
    return decorator
