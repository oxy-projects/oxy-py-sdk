from dataclasses import dataclass, field
from enum import Enum
from functools import cached_property
from json import JSONDecodeError
from typing import Any, Callable

from httpx import URL, Request, Response, QueryParams
from pydantic import BaseModel

from oxy.utils.lang.charset import Charset

ContentTypeName = "Content-Type"


class HttpUrl:
    def __init__(
        self,
        host_or_url: str,
        *,
        path: str | Callable[[], str] | None = None,
        query_params: QueryParams | Callable[[], QueryParams] | None = None,
    ):
        if host_or_url is None or host_or_url == "":
            raise ValueError("请输入`host_or_url`")
        self._host_or_url = host_or_url
        self._path = self.resolve_path(path)
        self._query_params = self.resolve_query_params(query_params)

    @staticmethod
    def resolve_path(path: str | Callable[[], str] | None = None) -> str | None:
        _resolved_path = path() if callable(path) else path
        _resolved_path = _resolved_path if _resolved_path != "" else None
        return (
            "/" + _resolved_path
            if _resolved_path is not None and not _resolved_path.startswith("/")
            else _resolved_path
        )

    @staticmethod
    def resolve_query_params(
        query_params: QueryParams | Callable[[], QueryParams] | None = None,
    ) -> QueryParams:
        _query_params = query_params() if callable(query_params) else query_params
        _query_params = _query_params or {}
        return QueryParams(_query_params)

    def format_url_path(self, **kwargs) -> HttpUrl:
        """
        替换路径上的参数。
        例如：https://example.com/{a}/{b}?c={c} & {'a':1,'b':2,'c':3} ==> https://example.com/1/2?c=3
        """
        _host_or_url = self._host_or_url.format(**kwargs)
        _path = self._path = (
            self._path.format(**kwargs)
            if  self._path is not None and self._path != "" else
            None
        )
        return HttpUrl(
            host_or_url=_host_or_url,
            path=_path,
            query_params=self._query_params,
        )

    @staticmethod
    def merge_query_params(
        path_params: QueryParams | None = None,
        req_params: QueryParams | Callable[[], QueryParams] | None = None,
    ) -> QueryParams:
        _path_query_params = path_params or {}
        _req_query_params = req_params() if callable(req_params) else req_params
        _req_query_params = _req_query_params or {}
        return (
            path_params.merge(_req_query_params)
            if path_params else
            QueryParams(_req_query_params)
        )

    @cached_property
    def url(self) -> URL:
        _url_with_path = (
            URL(url=self._host_or_url, path=self._path)
            if self._path is not None and self._path != "" else
            URL(url=self._host_or_url)
        )
        _path = _url_with_path.path
        _host_path = str(_url_with_path.join(_path))
        _query_params = self.merge_query_params(
            path_params=_url_with_path.params,
            req_params=self._query_params,
        )
        return URL(url=_host_path, params=_query_params)

    def copy_with(
        self,
        *,
        path: str | None = None,
        query_params: QueryParams | None = None
    ) -> HttpUrl:
        _path = path if path is not None and path != "" else self._path
        _query_params = query_params if query_params else self._query_params
        return HttpUrl(
            host_or_url=self._host_or_url,
            path=_path,
            query_params=_query_params,
        )

    def __str__(self) -> str:
        return str(self.url)


class RequestUrl(HttpUrl):
    def __init__(
        self,
        host_or_url: str,
        *,
        path: str | Callable[[], str] | None = None,
    ):
        super().__init__(host_or_url, path=path)

@dataclass(frozen=True)
class HttpRequest:
    data: str | bytes | dict[str, Any] | None = None
    extra: HttpRequestExtra | None = None


@dataclass(frozen=True)
class HttpRequestExtra:
    headers: dict[str, Any] = field(default_factory=dict)
    context: dict[str, Any] = field(default_factory=dict)
    query_params: QueryParams | None = None
    resp_model: type[BaseModel] | None = None
    is_resp_json: bool = False
    is_resp_curl: bool = False


class HttpResponse(Response):
    """
    Curl-debug stub response that mirrors the httpx Response attributes used by
    `_common_response_parser` (status_code / text / raise_for_status / json).
    """
    def __init__(self, status_code: int, text: str, *, request: Request):
        super().__init__(
            status_code=status_code,
            text=text,
            request=request,
        )

    def json(self, **kwargs: Any) -> Any:
        raise JSONDecodeError('不支持格式化', '{}', 0)


class MediaType(Enum):
    ALL = ("*", "*", None)

    APPLICATION_ATOM_XML = ("application", "atom+xml", True)
    APPLICATION_CBOR = ("application", "cbor", True)
    APPLICATION_FORM_URLENCODED = ("application", "x-www-form-urlencoded",True)
    APPLICATION_JSON = ("application", "json", False)
    APPLICATION_OCTET_STREAM = ("application", "octet-stream", True)
    APPLICATION_PDF = ("application", "pdf", True)
    APPLICATION_PROBLEM_JSON = ("application", "problem+json", False)
    APPLICATION_PROBLEM_XML = ("application", "problem+xml", True)
    APPLICATION_RSS_XML = ("application", "rss+xml", True)
    APPLICATION_SOAP_XML = ("application", "soap+xml", True)
    APPLICATION_STREAM_JSON = ("application", "stream+json", True)
    APPLICATION_SVG_XML = ("application", "svg+xml", True)
    APPLICATION_XHTML_XML = ("application", "xhtml+xml", True)
    APPLICATION_XML = ("application", "xml", True)

    IMAGE_BMP = ("image", "bmp", True)
    IMAGE_GIF = ("image", "gif", True)
    IMAGE_JPEG = ("image", "jpeg", True)
    IMAGE_PNG = ("image", "png", True)
    IMAGE_SVG = ("image", "svg+xml", True)
    IMAGE_TIFF = ("image", "tiff", True)
    IMAGE_WEBP = ("image", "webp", True)

    MULTIPART_FORM_DATA = ("multipart", "form-data", True)
    MULTIPART_MIXED = ("multipart", "mixed", True)
    MULTIPART_RELATED = ("multipart", "related", True)

    TEXT_EVENT_STREAM = ("text", "event-stream", True)
    TEXT_HTML = ("text", "html", True)
    TEXT_MARKDOWN = ("text", "markdown", True)
    TEXT_PLAIN = ("text", "plain", True)
    TEXT_XML = ("text", "xml", True)

    def __init__(
        self,
        type_: str,
        subtype: str,
        use_charset: bool,
    ):
        self.type = type_
        self.subtype = subtype
        self.use_charset = use_charset

    @property
    def mime_type(self) -> str:
        return f"{self.type}/{self.subtype}"

    def __str__(self) -> str:
        return self.mime_type

    def with_charset(self, charset: Charset) -> str:
        return (
            f"{self.mime_type}; charset={charset.upper()}"
            if self.use_charset else
            self.mime_type
        )

    @classmethod
    def of(cls, mime_type: str | None) -> "MediaType | None":
        """匹配媒体类型，忽略大小写、首尾空白和分号后的参数。

        空值返回 None；未定义的媒体类型抛出 ValueError。
        """
        if mime_type is None:
            return None

        assert isinstance(mime_type, str), "`mime_type`类型错误"
        normalized = mime_type.strip()
        if not normalized:
            return None

        normalized = normalized.split(";", 1)[0].strip().lower()
        for member in cls:
            if member.mime_type == normalized:
                return member

        raise ValueError(f"Unsupported media type: {mime_type!r}")


# 重命名
ContentType = MediaType
