from typing import Any, Callable, List, Collection


def distinct(
    iterable: Collection[Any],
    duplicate_field: Callable[[Any], Any] = lambda _v: _v,
) -> List[Any]:
    """
    去重
    """
    _duplicate = set()
    _result = []
    for i in iterable:
        val = duplicate_field(i)
        if val not in _duplicate:
            _result.append(i)
        _duplicate.add(val)
    return _result


def duplicate(
    iterable: Collection[Any],
    duplicate_field: Callable[[Any], Any] = lambda _v: _v,
) -> List[Any]:
    """
    取重复部分
    :param duplicate_field: 校验的字段
    """
    _duplicate = set()
    _result = []
    for i in iterable:
        val = duplicate_field(i)
        if val in _duplicate:
            _result.append(i)
        _duplicate.add(val)
    return _result
