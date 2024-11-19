# Copyright (C) 2024 Eneo Tecnologia S.L.
#
# Authors:
# Miguel Álvarez Adsuara <malvarez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify it under the terms of the
# GNU Affero General Public License as published by the Free Software Foundation, either version 3
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without
# even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License along with this program.
# If not, see <https://www.gnu.org/licenses/>.

import json
import unittest
import pandas as pd
from resources.src.ai.outliers_identifier import OutlierIdentifier

class TestOutlierIdentifier(unittest.TestCase):

    def setUp(self):
        self.identifier = OutlierIdentifier()

    def test_prepare_data_valid_input(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {"bytes": 500}},
                {"timestamp": "2024-11-14T12:05:00", "result": {"bytes": 300}}
            ]
        }
        self.identifier.prepare_data(data)
        self.assertIsInstance(self.identifier.df, pd.DataFrame)
        self.assertIn('timestamp', self.identifier.df.columns)
        self.assertIn('bytes', self.identifier.df.columns)
        self.assertEqual(len(self.identifier.df), 2)

    def test_prepare_data_missing_bytes(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {}},
                {"timestamp": "2024-11-14T12:05:00", "result": {}}
            ]
        }
        self.identifier.prepare_data(data)
        self.assertEqual(self.identifier.df['bytes'].sum(), 0)

    def test_prepare_data_empty_input(self):
        data = {}
        self.identifier.prepare_data(data)
        self.assertTrue(self.identifier.df.empty)

    def test_train_model_valid_data(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {"bytes": 500}},
                {"timestamp": "2024-11-14T12:05:00", "result": {"bytes": 300}},
                {"timestamp": "2024-11-14T12:10:00", "result": {"bytes": 1000}},
                {"timestamp": "2024-11-14T12:15:00", "result": {"bytes": 700}},
                {"timestamp": "2024-11-14T12:20:00", "result": {"bytes": 0}}
            ]
        }
        self.identifier.prepare_data(data)
        try:
            self.identifier.train_model(self.identifier.df[['hour', 'minute', 'day', 'dayofweek', 'dayofyear', 'rolling_mean', 'rolling_std', 'low_traffic']])
        except Exception as e:
            self.fail(f"Training failed with exception: {e}")

    def test_identify_implicated_ips_no_outliers(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {"bytes": 100}},
                {"timestamp": "2024-11-14T12:05:00", "result": {"bytes": 100}}
            ]
        }
        outliers = []
        self.identifier.prepare_data(data)
        self.identifier.train_model(self.identifier.df[['hour', 'minute', 'day', 'dayofweek', 'dayofyear', 'rolling_mean', 'rolling_std', 'low_traffic']])
        result = self.identifier.identify_implicated_ips(outliers)
        self.assertEqual(result, {"ips": []})

    def test_identify_implicated_ips_with_outliers(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {"bytes": 100}},
                {"timestamp": "2024-11-14T12:05:00", "result": {"bytes": 1000}},  # Anomalous traffic
                {"timestamp": "2024-11-14T12:10:00", "result": {"bytes": 100}},
            ]
        }
        outliers = [{"timestamp": "2024-11-14T12:05:00"}]
        self.identifier.prepare_data(data)
        self.identifier.train_model(self.identifier.df[['hour', 'minute', 'day', 'dayofweek', 'dayofyear', 'rolling_mean', 'rolling_std', 'low_traffic']])
        result = self.identifier.identify_implicated_ips(outliers)
        self.assertIn("192.168.1.1", result["ips"][0]["caused_by"])

    def test_execute_with_valid_input(self):
        data = {
            "192.168.1.1": [
                {"timestamp": "2024-11-14T12:00:00", "result": {"bytes": 500}},
                {"timestamp": "2024-11-14T12:05:00", "result": {"bytes": 300}},
                {"timestamp": "2024-11-14T12:10:00", "result": {"bytes": 1000}}
            ]
        }
        outliers = [{"timestamp": "2024-11-14T12:10:00"}]
        result = self.identifier.execute(outliers, data)
        self.assertIsInstance(result, str)
        parsed_result = json.loads(result)
        self.assertIn("ips", parsed_result)
        self.assertEqual(len(parsed_result["ips"]), 1)

    def test_train_and_execute_model_error_handling(self):
        data = None  # Invalid data
        outliers = [{"timestamp": "2024-11-14T12:10:00"}]
        result = self.identifier.train_and_execute_model(outliers, data)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "error")

    def test_return_error(self):
        error_message = "Test error"
        result = self.identifier.return_error(error_message)
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["msg"], error_message)

if __name__ == "__main__":
    unittest.main()
