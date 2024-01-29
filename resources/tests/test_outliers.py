# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import unittest
import os
import sys
import json
import tempfile

from resources.src.ai.outliers import Autoencoder

class TestAutoencoder(unittest.TestCase):
    main_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(current_dir, "outliers_test_data.json")
        with open(data_file_path, "r") as data_file:
            self.sample_data = json.load(data_file)

    def test_model_execution_with_no_data(self):
        result = Autoencoder.execute_prediction_model(
            {},
            "bytes",
            os.path.join(self.main_dir, "ai", "traffic.keras"),
            os.path.join(self.main_dir, "ai", "traffic.ini")
        )
        self.assertEqual(
            result['status'],
            'error'
        )
    def test_model_execution_with_no_metric(self):
        result = Autoencoder.execute_prediction_model(
            self.sample_data,
            "",
            os.path.join(self.main_dir, "ai", "traffic.keras"),
            os.path.join(self.main_dir, "ai", "traffic.ini")
        )
        self.assertEqual(
            result['status'],
            'error'
        )
    def test_model_execution_with_sample_data(self):
        Autoencoder.execute_prediction_model(
            self.sample_data,
            "bytes",
            os.path.join(self.main_dir, "ai", "traffic.keras"),
            os.path.join(self.main_dir, "ai", "traffic.ini")
        )
    def test_invalid_model(self):
        with self.assertRaises(FileNotFoundError):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "test.keras"),
                os.path.join(self.main_dir, "ai", "traffic.ini")
            )

    def test_invalid_config(self):
        with self.assertRaises(FileNotFoundError):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "traffic.keras"),
                os.path.join(self.main_dir, "ai", "test.ini")
            )

    def test_load_empty_model(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        with self.assertRaises(Exception):
            Autoencoder(
                os.path.join(temp_file_path),
                os.path.join(self.main_dir, "ai", "traffic.ini")
            )

    def test_load_empty_conifg(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        with self.assertRaises(Exception):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "traffic.keras"),
                os.path.join(temp_file_path)
            )

if __name__ == '__main__':
    unittest.main()
