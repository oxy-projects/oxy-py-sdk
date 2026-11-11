import unittest
from datetime import datetime, timedelta

import pandas as pd

from oxy.utils.lang import timestamp_millis, gen_uuid_str, hide_error, split
from oxy.utils.lang.path import traverse_folder
from tests.config import project_resources


def raise_exp():
    raise RuntimeError('测试异常')


@hide_error()
def raise_exp_hide():
    raise_exp()


class LangTestCase(unittest.TestCase):
    def test_timestamp_millis(self):
        ts = timestamp_millis()
        self.assertIsInstance(ts, int)
        self.assertGreater(ts, 0)

    def test_uuid(self):
        uid = gen_uuid_str()
        self.assertIsInstance(uid, str)
        self.assertGreater(len(uid), 0)

    def test_hide_error(self):
        self.assertRaises(RuntimeError, raise_exp)
        self.assertIsNone(raise_exp_hide())

    def test_project_path(self):
        root = project_resources()
        self.assertTrue(root.exists())
        paths = traverse_folder(root)
        self.assertGreater(len(paths), 0)

    def test_split(self):
        data_df = pd.DataFrame([{'a': 1}, {'a': 2}, {'a': 3}, {'a': 4}, {'a': 5}])
        parts = list(split(data_df, 2))
        self.assertEqual(len(parts), 3)
        self.assertEqual(len(parts[0]), 2)

        date_parts = list(split((datetime(2024, 7, 10), datetime(2024, 7, 20)), timedelta(days=3)))
        self.assertGreaterEqual(len(date_parts), 3)

        num_parts = list(split((13, 51), 3))
        self.assertGreater(len(num_parts), 0)


if __name__ == '__main__':
    unittest.main()
