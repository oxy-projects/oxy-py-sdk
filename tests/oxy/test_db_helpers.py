import unittest

import pandas as pd

from ziroom.utils.db._db import empty, in_sql, submit_dml_sql


class DbHelpersTestCase(unittest.TestCase):
    def test_empty(self):
        self.assertTrue(empty(None))
        self.assertTrue(empty(''))
        self.assertFalse(empty('x'))
        self.assertTrue(empty([]))
        self.assertFalse(empty([1]))
        self.assertTrue(empty(pd.DataFrame()))
        self.assertFalse(empty(pd.DataFrame([{'a': 1}])))

    def test_in_sql(self):
        self.assertEqual(in_sql(['a', 'b']).strip(), "('a','b')")
        with self.assertRaises(Exception):
            in_sql([])

    def test_submit_dml_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            submit_dml_sql(1, 1, 'c', 'select 1')


if __name__ == '__main__':
    unittest.main()
