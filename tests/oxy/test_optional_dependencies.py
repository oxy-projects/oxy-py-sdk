"""Data extra integration checks."""


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
