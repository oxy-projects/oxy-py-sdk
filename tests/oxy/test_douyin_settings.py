import unittest

from oxy.apis.抖音._settings import dy_url, dy_headers
from oxy.utils.http.api import make_response_processors, origin_response


class DouyinSettingsTestCase(unittest.TestCase):
    def test_dy_url_lazy(self):
        url_fn = dy_url('/api/apps/trade/v2/order/query_order')
        self.assertTrue(callable(url_fn))
        self.assertTrue(url_fn().endswith('/api/apps/trade/v2/order/query_order'))

    def test_dy_headers(self):
        self.assertEqual(dy_headers('abc'), {'access-token': 'abc'})

    def test_make_response_processors_ignores(self):
        processors = make_response_processors(ignores=['parser'])
        self.assertIn('success', processors)
        self.assertIn('error_msg', processors)
        self.assertNotIn('parser', processors)
        self.assertEqual(set(origin_response().keys()), {'success', 'error_msg', 'parser'})


if __name__ == '__main__':
    unittest.main()
