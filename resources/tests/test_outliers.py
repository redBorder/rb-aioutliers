# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest
import os
import sys
import logging
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ai.outliers import Autoencoder

class TestAutoencoder(unittest.TestCase):
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(current_dir, "outliers_test_data.json")

        with open(data_file_path, "r") as data_file:
            self.sample_data = json.load(data_file)

    def test_model_execution_with_no_data(self):
        with self.assertRaises(Exception):
            Autoencoder.execute_prediction_model(
                {},
                "bytes",
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ai", "traffic.keras"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ai", "traffic.ini")
            )
    def test_model_execution_with_sample_data(self):
        Autoencoder.execute_prediction_model(
            self.sample_data,
            "bytes",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ai", "traffic.keras"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ai", "traffic.ini")
        )

if __name__ == '__main__':
    unittest.main()
