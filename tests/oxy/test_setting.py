import unittest

from oxy.utils import setting
from oxy.utils.setting._setting import _redact_for_log
from tests.config import project_settings


@setting.read('project.name', settings=project_settings)
def name():
    pass


@setting.read('app.name-unknown')
def name_unknown():
    return '未知项目'


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
