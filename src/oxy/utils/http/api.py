from http import HTTPMethod
from typing import Callable, Any, List, Optional, Literal

from oxy.utils.http._api import (
    _default_success,
    _default_error_msg,
    _default_response_parser,
    _http,
)
from oxy.utils.http._model import ContentType, RequestUrl
from oxy.utils.lang.charset import Charset

ResponseProcessor = Literal["success", "error_msg", "parser"]


def make_response_processors(
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
    ignores: Optional[ResponseProcessor | List[ResponseProcessor]] = None,
) -> dict:
    """
    构造 HTTP 响应处理三件套（success / error_msg / parser）。
    """
    if isinstance(ignores, str):
        ignores = [ignores]
    all_keys = {
        'success': success,
        'error_msg': error_msg,
        'parser': parser,
    }
    for key in ignores or []:
        all_keys.pop(key, None)
    return all_keys


def origin_response(
    ignores: Optional[ResponseProcessor | List[ResponseProcessor]] = None
) -> dict:
    return make_response_processors(ignores=ignores)


def get(
    url: str | RequestUrl | Callable[[], RequestUrl],
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
) -> Callable[[Any], Any]:
    """
    GET 请求
    """
    return http(
        url=url,
        method=HTTPMethod.GET,
        success=success,
        error_msg=error_msg,
        parser=parser,
    )


def get_json(
    url: str | RequestUrl | Callable[[], RequestUrl],
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
) -> Callable[[Any], Any]:
    """
    GET JSON 请求
    """
    return http(
        url=url,
        method=HTTPMethod.GET,
        content_type=ContentType.APPLICATION_JSON,
        success=success,
        error_msg=error_msg,
        parser=parser,
    )


def post(
    url: str | RequestUrl | Callable[[], RequestUrl],
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
) -> Callable[[Any], Any]:
    """
    POST 请求
    """
    return http(
        url=url,
        method=HTTPMethod.POST,
        content_type=ContentType.APPLICATION_FORM_URLENCODED,
        success=success,
        error_msg=error_msg,
        parser=parser,
    )


def post_json(
    url: str | RequestUrl | Callable[[], RequestUrl],
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
) -> Callable[[Any], Any]:
    """
    POST JSON 请求
    """
    return http(
        url=url,
        method=HTTPMethod.POST,
        content_type=ContentType.APPLICATION_JSON,
        success=success,
        error_msg=error_msg,
        parser=parser,
    )


def http(
    url: str | RequestUrl | Callable[[], RequestUrl],
    method: HTTPMethod = HTTPMethod.GET,
    content_type: ContentType = ContentType.ALL,
    charset: Charset = Charset.UTF_8,
    *,
    success: Callable[[Any], bool] = _default_success,
    error_msg: Callable[[Any], Optional[str]] = _default_error_msg,
    parser: Callable[[Any, Any], Any] = _default_response_parser,
) -> Callable[[Any], Any]:
    """
    HTTP 请求
    """
    return _http(
        url=url,
        method=method,
        content_type=content_type,
        charset=charset,
        success=success,
        error_msg=error_msg,
        resp_parser=parser,
    )
