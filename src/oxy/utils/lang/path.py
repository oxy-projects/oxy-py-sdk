import inspect
import os
from functools import wraps
from pathlib import Path
from typing import Callable, Any


def project_path(*, parent_level: int = 0):
    """
    获取项目路径
    :param parent_level: 有几层父目录
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            nonlocal parent_level

            func_path = Path(inspect.getsourcefile(func)) # type: ignore
            for i in range(parent_level + 1):
                func_path = func_path.parent
            return func_path
        return wrapper
    return decorator


def traverse_folder(folder_path: os.PathLike, parser: Callable[[Path], Any] = lambda fp00: fp00):
    # 遍历文件夹下的所有文件
    result = {}
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            fp = Path(root).joinpath(file)
            result[str(fp.absolute())] = parser(fp)
    return result
