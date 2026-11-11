from datetime import datetime, timedelta
from typing import overload


@overload
def split(data: list, delta: int) -> list[list]: ...
@overload
def split(data: tuple[datetime, datetime], delta: timedelta) -> list[tuple[datetime, datetime]]: ...
@overload
def split(data: tuple[int, int], delta: int) -> list[tuple[int, int]]: ...


def split(
    data: list | tuple[datetime, datetime] | tuple[int, int],
    delta: int | timedelta
) -> list[list] | list[tuple[datetime, datetime]] | list[tuple[int, int]]:
    """
    如果是集合：[e1, e2, e3, ..., en] ==> [[e1, e2], [e3, e4], ..., [en-1, en]] ；
    如果是范围：[开始，结束) ==> [开始，开始+30)，[开始+30，开始+60)，...，[开始+30*N，结束) ；
    """
    if data is None:
        return []
    if isinstance(data, list):
        assert isinstance(delta, int)
        return _split_list(data, delta)
    if isinstance(data, tuple):
        # tuple代表一个范围
        if len(data) < 2:
            raise Exception('请输入分割范围')
        if isinstance(data[0], datetime) and isinstance(data[1], datetime):
            assert isinstance(delta, timedelta), '日期分割间隔类型错误'
            return _split_date(data[0], data[1], delta)
        elif isinstance(data[0], int) and isinstance(data[1], int):
            assert isinstance(delta, int), '数字分割间隔类型错误'
            return _split_number(data[0], data[1], delta)
    raise TypeError('暂不支持的操作类型')


def _split_list(data: list, group_size: int) -> list[list]:
    if not data:
        return []
    idx = 0
    page = group_size
    all_data = []
    while True:
        idx += 1
        part = data[page * (idx - 1): page * idx]
        if not part:
            break
        all_data.append(part)
    return all_data


def _split_date(start: datetime, end: datetime, delta_t: timedelta = timedelta(days=30)) -> list[tuple[datetime, datetime]]:
    """
    [开始，结束) ==> [开始，开始+30)，[开始+30，开始+60)，...，[开始+30*N，结束)
    :param start: 开始时间
    :param end: 结束时间，不包含这个时间点
    :param delta_t: 切割依据的时间间隔
    """
    periods = []
    while True:
        next_start = start + delta_t
        if next_start >= end:
            periods.append((start, end))
            break
        else:
            periods.append((start, next_start))
        start = next_start
    return periods


def _split_number(start: int, end: int, delta_n: int) -> list[tuple[int, int]]:
    if start is None or end is None or start > end:
        return []
    return [(i, i + delta_n if i + delta_n <= end else end) for i in range(start, end + 1, delta_n) if i < end]
