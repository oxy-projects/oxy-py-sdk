import asyncio as _asyncio
import inspect as _inspect
import tempfile as _tempfile
from functools import wraps
from os import PathLike
from pathlib import Path

import pandas as pd


def _read_cached_excel(file: Path) -> pd.DataFrame | None:
    if file.exists():
        return pd.read_excel(file)
    return None


def _write_excel_atomically(result: pd.DataFrame, file: Path) -> None:
    with _tempfile.NamedTemporaryFile(dir=file.parent, suffix=file.suffix, delete=False) as temporary:
        temporary_path = Path(temporary.name)

    try:
        result.to_excel(temporary_path, index=False)
        temporary_path.replace(file)
    finally:
        temporary_path.unlink(missing_ok=True)


def cached_excel(file: str | PathLike[str], *, home: bool = False):
    """
    表格文件缓存。装饰异步函数时在线程中读写 Excel。
    """
    def decorator(func):
        if _inspect.iscoroutinefunction(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                target = Path.home().joinpath(file) if home else Path(file)
                cached = await _asyncio.to_thread(_read_cached_excel, target)
                if cached is not None:
                    return cached
                result = await func(*args, **kwargs)
                if isinstance(result, pd.DataFrame):
                    await _asyncio.to_thread(_write_excel_atomically, result, target)
                return result
            return async_wrapper

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
