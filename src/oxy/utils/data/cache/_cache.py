from functools import wraps
from os import PathLike
from pathlib import Path

import pandas as pd


def cached_excel(file: str | PathLike[str], *, home: bool = False):
    """
    表格文件缓存
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal file
            nonlocal home

            if home:
                file = Path.home().joinpath(file)
            if isinstance(file, str):
                file = Path(file)
            if not file.exists():
                result = func(*args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    result.to_excel(file, index=False)
            else:
                result = pd.read_excel(file)
            return result
        return wrapper
    return decorator
