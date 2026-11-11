import unittest

from oxy.utils.lang.collection import distinct, duplicate


class CollectionTestCase(unittest.TestCase):
    def test_distinct(self):
        arr = [
            {'a': 1, 'b': 1},
            {'a': 1, 'b': 2},
            {'a': 1, 'b': 1},
            {'a': 2, 'b': 3},
            {'a': 3, 'b': 3},
        ]
        by_pair = distinct(arr, lambda i: (i['a'], i['b']))
        self.assertEqual(len(by_pair), 4)
        by_b = distinct(arr, lambda i: i['b'])
        self.assertEqual(len(by_b), 3)

    def test_duplicate(self):
        arr = ['a', 'a', 'b', 'c', 'b']
        self.assertEqual(distinct(arr), ['a', 'b', 'c'])
        self.assertEqual(duplicate(arr), ['a', 'b'])


if __name__ == '__main__':
    unittest.main()
