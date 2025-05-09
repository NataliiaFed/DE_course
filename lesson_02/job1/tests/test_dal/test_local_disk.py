"""
Tests dal.local_disk.py module
"""
import tempfile
import os
import json
from unittest import TestCase, mock

from lesson_02.job1.dal.local_disk import save_to_disk


class SaveToDiskTestCase(TestCase):
    """
    Test dal.local_disk.save_to_disk function.
    """

    def test_save_to_disk_writes_json_file(self):
        sample_data = [{"client": "Test User", "product": "Phone", "price": 100}]
        with tempfile.TemporaryDirectory() as tmpdir:
            save_dir = os.path.join(tmpdir, "2022-08-09")

            save_to_disk(sample_data, save_dir)

            expected_file_path = os.path.join(save_dir, "sales_2022-08-09.json")

            self.assertTrue(os.path.exists(expected_file_path))

            with open(expected_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.assertEqual(data, sample_data)
