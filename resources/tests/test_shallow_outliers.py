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
import numpy as np

from resources.src.ai.shallow_outliers import ShallowOutliers

class TestShallowOutliers(unittest.TestCase):

    def setUp(self):
        self.model= ShallowOutliers()

    def test_prediction_empty_array(self):
        with self.assertRaises(ValueError):
            self.model.predict(np.array([]))

    def test_prediction_non_1d_array(self):
        with self.assertRaises(ValueError):
            self.model.predict(np.array([[1, 2], [3, 4]]))

    def test_prediction_non_numeric_array(self):
        with self.assertRaises(ValueError):
            self.model.predict(np.array(['a', 'b', 'c']))

    def test_prediction_shape(self):
        arr = np.array([1,2,3,4,5,6,7,8,9])
        result = self.model.predict(arr)
        np.testing.assert_allclose(result.shape, arr.shape)

    def test_prediction_identical_values(self):
        arr = np.array([1, 1, 1, 1, 1, 1])
        result = self.model.predict(arr)
        np.testing.assert_allclose(result, arr)

    def test_prediction_integer_input(self):
        arr = np.array([1, 2, 3, 4, 5], dtype=int)
        try:
            self.model.predict(arr)
        except Exception as e:
            self.fail(f"An exception occurred: {e}")

    def test_get_anomalies_obvious_anomalies(self):
        arr = np.random.rand(1000)
        arr[[100,200,500]]=100
        smoothed_arr = self.model.predict(arr)
        outliers = self.model.get_outliers(arr, smoothed_arr)
        self.assertTrue(np.all(outliers[arr == 100]))

    def test_compute_json_valid_data(self):
        valid_json =[
            {"timestamp": "2023-01-01T00:00:00", "result": {"value": 1}},
            {"timestamp": "2023-01-01T01:00:00", "result": {"value": 2}},
            {"timestamp": "2023-01-01T02:00:00", "result": {"value": 3}},
            {"timestamp": "2023-01-01T03:00:00", "result": {"value": 4}},
        ]
        try:
            self.model.compute_json(valid_json)
        except Exception as e:
            self.fail(f"An exception occurred: {e}")

    def test_compute_json_output_format(self):
        sample_json =[
            {"timestamp": "2023-01-01T00:00:00", "result": {"value": 1}},
            {"timestamp": "2023-01-01T01:00:00", "result": {"value": 1}},
            {"timestamp": "2023-01-01T02:00:00", "result": {"value": 1000}},
            {"timestamp": "2023-01-01T03:00:00", "result": {"value": 1}},
            {"timestamp": "2023-01-01T03:00:00", "result": {"value": 1}},
        ]
        result = self.model.compute_json(sample_json)
        self.assertIsInstance(result, dict)
        self.assertIn('anomalies', result)
        self.assertIn('predicted', result)
        self.assertIn('status', result)
        for entry in result['anomalies']:
            self.assertTrue(isinstance(entry, dict))
            self.assertIn('timestamp', entry)
            self.assertIn('expected', entry)
        for entry in result['predicted']:
            self.assertTrue(isinstance(entry, dict))
            self.assertIn('timestamp', entry)
            self.assertIn('forecast', entry)

if __name__ == "__main__":
    unittest.main()
