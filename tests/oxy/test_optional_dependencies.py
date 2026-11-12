"""Exercise imports in a subprocess without any site-packages installed."""
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run_without_dependencies(code):
    return subprocess.run(
        [sys.executable, '-S', '-c', code],
        env={**os.environ, 'PYTHONPATH': str(ROOT / 'src')},
        capture_output=True, text=True,
    )


def test_base_utilities_need_no_third_party_packages():
    result = run_without_dependencies('''
import oxy
from oxy.utils.lang import split, gen_uuid_str
from oxy.utils.lang.collection import distinct
from oxy.utils.codec import md5, sha256
from oxy.utils.setting import read, convert_setting
assert gen_uuid_str()
assert distinct([1, 1, 2]) == [1, 2]
assert convert_setting({'a': 1}, str) == {'a': '1'}
''')
    assert result.returncode == 0, result.stderr


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
