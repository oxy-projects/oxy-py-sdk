import logging
from logging import Formatter, Logger
from typing import Mapping, Any, Literal

try:
    from colorama import Fore, Style
except ModuleNotFoundError:
    # Keep base utilities usable without optional terminal styling.
    class Fore:
        GREEN = BLUE = YELLOW = RED = ''

    class Style:
        RESET_ALL = ''


def _choose_logging_color(record: logging.LogRecord):
    if not record or not record.levelno:
        return None
    match record.levelno:
        case logging.NOTSET | logging.DEBUG:
            return Fore.GREEN
        case logging.INFO:
            return Fore.BLUE
        case logging.WARN:
            return Fore.YELLOW
        case logging.ERROR | logging.FATAL:
            return Fore.RED
        case _:
            return None


class OxyFormatter(Formatter):

    def __init__(
        self,
        fmt: str | None = "%(asctime)s.%(msecs)03d | %(levelname)s | [%(name)s.%(funcName)s] - %(message)s",
        datefmt: str | None = "%Y-%m-%d %H:%M:%S",
        style: Literal["%", "{", "$"] = "%",
        validate: bool = True,
        *,
        defaults: Mapping[str, Any] | None = None,
    ):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)


class OxyConsoleFormatter(OxyFormatter):

    def formatMessage(self, record: logging.LogRecord):
        msg = self._style.format(record)
        _clr = _choose_logging_color(record)
        if _clr is None:
            return msg
        return _clr + msg + Style.RESET_ALL


def of(name=None) -> Logger:
    """
    获取日志实例
    """
    _log = logging.getLogger(name)
    _log.setLevel(logging.DEBUG)
    return _log
