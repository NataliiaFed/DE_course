"""
Tests sales_api.py module.
"""
from unittest import TestCase, mock
import os

# NB: avoid relative imports when you will write your code:
from lesson_02.job1.dal.sales_api import get_sales


class GetSalesTestCase(TestCase):
    """
    Test sales_api.get_sales function.
    """

    @mock.patch.dict(os.environ, {"AUTH_TOKEN": "test_token"})
    @mock.patch("lesson_02.job1.dal.sales_api.requests.get")
    def test_get_sales_multiple_pages(self, mock_get):
        mock_get.side_effect = [
            mock.Mock(status_code=200, json=lambda: [{"client": "A"}]),
            mock.Mock(status_code=200, json=lambda: [{"client": "B"}]),
            mock.Mock(status_code=200, json=lambda: [])
        ]

        result = get_sales("2022-08-09")
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["client"], "A")
        self.assertEqual(result[1]["client"], "B")

    @mock.patch.dict(os.environ, {}, clear=True)
    def test_get_sales_no_token(self):
        with self.assertRaises(EnvironmentError):
            get_sales("2022-08-09")
