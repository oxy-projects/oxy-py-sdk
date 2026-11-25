"""Data extra integration checks."""

import asyncio
from inspect import iscoroutinefunction
from pathlib import Path

import pytest


def test_excel_cache_round_trip(tmp_path):
    import pandas as pd
    from oxy.utils.data.cache import cached_excel

    calls = []

    @cached_excel(tmp_path / 'cache.xlsx')
    def load():
        calls.append(True)
        return pd.DataFrame({'value': [1, 2]})

    pd.testing.assert_frame_equal(load(), load())
    assert calls == [True]


def test_excel_cache_async_round_trip(tmp_path, monkeypatch):
    import pandas as pd
    from oxy.utils.data.cache import cached_excel

    monkeypatch.setattr(Path, 'home', lambda: tmp_path)
    calls = []

    @cached_excel('cache.xlsx', home=True)
    async def load(*, value):
        await asyncio.sleep(0)
        calls.append(value)
        return pd.DataFrame({'value': [value]})

    assert iscoroutinefunction(load)
    pd.testing.assert_frame_equal(asyncio.run(load(value=1)), asyncio.run(load(value=2)))
    assert (tmp_path / 'cache.xlsx').is_file()
    assert calls == [1]


def test_excel_cache_async_skips_non_dataframe(tmp_path):
    from oxy.utils.data.cache import cached_excel

    target = tmp_path / 'cache.xlsx'

    @cached_excel(target)
    async def load():
        return 'uncached'

    assert asyncio.run(load()) == 'uncached'
    assert not target.exists()


def test_excel_cache_async_concurrent_writes(tmp_path):
    import pandas as pd
    from oxy.utils.data.cache import cached_excel

    target = tmp_path / 'cache.xlsx'

    @cached_excel(target)
    async def load(ready, value):
        await ready.wait()
        return pd.DataFrame({'value': [value]})

    async def run():
        ready = asyncio.Barrier(2)
        return await asyncio.wait_for(
            asyncio.gather(load(ready, 1), load(ready, 2)), timeout=5,
        )

    results = asyncio.run(run())
    assert [result['value'].tolist() for result in results] == [[1], [2]]
    assert pd.read_excel(target)['value'].tolist() in ([1], [2])
    assert list(tmp_path.iterdir()) == [target]


def test_excel_cache_async_failed_write(tmp_path, monkeypatch):
    import pandas as pd
    from oxy.utils.data.cache import cached_excel

    target = tmp_path / 'cache.xlsx'

    @cached_excel(target)
    async def load():
        return pd.DataFrame({'value': [1]})

    def fail_write(self, path, **kwargs):
        path.write_bytes(b'incomplete')
        assert not target.exists()
        raise OSError('failed write')

    with monkeypatch.context() as patch:
        patch.setattr(pd.DataFrame, 'to_excel', fail_write)
        with pytest.raises(OSError, match='failed write'):
            asyncio.run(load())

    assert list(tmp_path.iterdir()) == []
    pd.testing.assert_frame_equal(asyncio.run(load()), pd.read_excel(target))
