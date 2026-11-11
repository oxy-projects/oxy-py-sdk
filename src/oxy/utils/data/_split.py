import pandas as pd


def split(
    data: pd.DataFrame,
    delta: int,
) -> list[pd.DataFrame]:
    """
    如果是集合：[e1, e2, e3, ..., en] ==> [[e1, e2], [e3, e4], ..., [en-1, en]] ；
    如果是范围：[开始，结束) ==> [开始，开始+30)，[开始+30，开始+60)，...，[开始+30*N，结束) ；
    """
    if data is None:
        return []
    if isinstance(data, pd.DataFrame):
        return _split_data_frame(data, delta)
    raise TypeError('暂不支持的操作类型')


def _split_data_frame(data: pd.DataFrame, group_size: int) -> list[pd.DataFrame]:
    if data is None or data.empty:
        return []
    idx = 0
    page = group_size
    all_data = []
    while True:
        idx += 1
        part = data.iloc[page * (idx - 1): page * idx]
        if part.empty:
            break
        all_data.append(part)
    return all_data
