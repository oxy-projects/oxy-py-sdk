import asyncio
import unittest
from inspect import iscoroutinefunction

import pytest

from oxy.utils import setting
from oxy.utils.lang import IllegalArgumentException
from oxy.utils.setting._setting import _redact_for_log
from tests.config import project_settings


@setting.read('project.name', settings=project_settings)
def name():
    pass


@setting.read('app.name-unknown')
def name_unknown():
    return '未知项目'


def test_read_async_config_and_parser(tmp_path):
    config_file = tmp_path / 'settings.yaml'
    config_file.write_text('application:\n  port: "8080"\n', encoding='utf-8')
    parsed = []

    @setting.config(config_dir=str(tmp_path))
    async def load():
        raise AssertionError('config replaces the function body')

    async def parse(value):
        await asyncio.sleep(0)
        parsed.append(value)
        return int(value)

    @setting.read('application.port', settings=load, parser=parse)
    async def port():
        raise AssertionError('configured values take precedence')

    assert iscoroutinefunction(load)
    assert iscoroutinefunction(port)
    assert asyncio.run(port()) == 8080
    config_file.unlink()
    assert asyncio.run(load()) == {'application': {'port': '8080'}}
    assert asyncio.run(port()) == 8080
    assert parsed == ['8080']


@pytest.mark.parametrize('settings_source', [{'value': '7'}, lambda: {'value': '7'}])
def test_read_async_supports_sync_callbacks(settings_source):
    @setting.read('value', settings=settings_source, parser=int)
    async def value():
        raise AssertionError('configured values take precedence')

    assert asyncio.run(value()) == 7


def test_read_async_awaits_values_from_sync_callbacks():
    async def resolve_settings():
        return {'value': 7}

    async def resolve_value(value):
        return value + 1

    @setting.read('value', settings=lambda: resolve_settings(), parser=lambda value: resolve_value(value))
    async def value():
        raise AssertionError('configured values take precedence')

    assert asyncio.run(value()) == 8


def test_read_async_uses_uncached_default():
    @setting.read('missing', settings={'value': 7})
    async def value(default):
        await asyncio.sleep(0)
        return default

    assert asyncio.run(value(default=0)) == 0
    assert asyncio.run(value(default=5)) == 5
    for invalid in (None, ''):
        with pytest.raises(IllegalArgumentException, match='missing'):
            asyncio.run(value(default=invalid))


@pytest.mark.parametrize('callback_name', ['settings', 'parser'])
def test_read_sync_rejects_async_callbacks(callback_name):
    async def callback(*args):
        raise AssertionError('callbacks are not invoked during decoration')

    with pytest.raises(TypeError, match=callback_name):
        setting.read('value', **{callback_name: callback})(lambda: None)


class SettingTestCase(unittest.TestCase):
    def test_read_existing(self):
        self.assertEqual(name(), 'hello world')

    def test_read_default(self):
        self.assertEqual(name_unknown(), '未知项目')

    def test_redact_sensitive_keys(self):
        self.assertEqual(_redact_for_log('zir.worktop.web-token', 'secret-jwt'), '***')
        self.assertEqual(_redact_for_log('project.name', 'hello'), 'hello')


if __name__ == '__main__':
    unittest.main()
