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

import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.server.rest import APIServer

class TestAPIServer(unittest.TestCase):
    output_data = {
        "anomalies": [{'expected': 1, 'timestamp': '2023-09-21T09:00:00.000Z'}],
        "predicted": [{'forecast': 1, 'timestamp': '2023-09-21T09:00:00.000Z'}],
        "status": "success"
    }

    def setUp(self):
        self.api_server = APIServer()

    def tearDown(self):
        pass

    def test_calculate_endpoint_missing_query(self):
        data = {'model':'YXNkZg=='}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Error decoding query', 'status': 'error'}
            )

    def test_calculate_endpoint_invalid_query(self):
        data = {'model':'YXNkZg==', 'query':'YXNkZg=='}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Error decoding query', 'status': 'error'}
            )

    @patch('druid.client.DruidClient.execute_query')
    @patch('ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_invalid_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'YXNkZg==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('druid.client.DruidClient.execute_query')
    @patch('ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_unathorized_model_access(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'Li90ZXN0', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('druid.client.DruidClient.execute_query')
    @patch('ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_none_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('druid.client.DruidClient.execute_query')
    @patch('ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_invalid_b64_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'model', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('druid.client.DruidClient.execute_query')
    @patch('ai.outliers.Autoencoder.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_valid_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = True
        data = {'model':'YXNkZg==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('druid.client.DruidClient.execute_query')
    @patch('os.path.isfile')
    def test_execute_default_model_invalid_query(self, mock_isfile, mock_query):
        mock_query.return_value = {"test":"test"}
        mock_isfile.return_value = False
        data = {'model':'YXNkZg==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Error while calculating prediction model', 'status': 'error'}
            )

if __name__ == '__main__':
    unittest.main()
