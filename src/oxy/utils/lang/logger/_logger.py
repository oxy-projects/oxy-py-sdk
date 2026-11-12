import logging
from datetime import datetime, timezone
from logging import Formatter, Logger

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


_default_zone = datetime.now().astimezone().tzinfo


class OxyFormatter(Formatter):
    def formatTime(self, record, datefmt=None):
        """
        重写日志框架的日期格式化（仅作用于本 Formatter，不 monkeypatch 全局）。
        """
        ct = datetime.fromtimestamp(record.created, tz=timezone.utc).astimezone(_default_zone)
        if datefmt:
            return ct.strftime(datefmt)
        return ct.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

    def formatMessage(self, record: logging.LogRecord):
        msg = self._style.format(record)
        _clr = _choose_logging_color(record)
        if _clr is None:
            return msg
        return _clr + msg + Style.RESET_ALL


_handler = logging.StreamHandler()
_handler.setFormatter(OxyFormatter())
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | [%(name)s.%(funcName)s] - %(message)s",
    handlers=[_handler],
)


def of(name=None) -> Logger:
    """
    获取日志实例
    """
    _log = logging.getLogger(name)
    _log.setLevel(logging.DEBUG)
    return _log
