from functools import wraps

from oxy.utils.lang import logger

log = logger.of(__name__)


def hide_error(err_type: type[BaseException] = Exception):
    """
    隐藏异常
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except err_type as e:
                log.exception('<%s>调用异常：%s', func.__name__, str(e))
                return None
        return wrapper
    return decorator


class IllegalArgumentException(RuntimeError):
    pass
