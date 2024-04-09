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
import json
import base64
import unittest
from unittest.mock import patch

from resources.src.server.rest import APIServer

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
                {'msg': 'No data provided or requested', 'status': 'error'}
            )

    def test_calculate_endpoint_invalid_query(self):
        data = {'model':'YXNkZg==', 'query':'YXNkZg=='}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Error decoding json', 'status': 'error'}
            )

    def test_calculate_endpoint_druid_query_execution_malfunction(self):
        data = {'model':'YXNkZg==', 'query':'eyJ0ZXN0IjoidGVzdCJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Could not execute druid query', 'status': 'error'}
            )

    @patch('resources.src.druid.client.DruidClient.execute_query')
    @patch('resources.src.ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_invalid_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'YXNkZg==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('resources.src.druid.client.DruidClient.execute_query')
    @patch('resources.src.ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_unathorized_model_access(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'Li90ZXN0', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('resources.src.druid.client.DruidClient.execute_query')
    @patch('resources.src.ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_none_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('resources.src.druid.client.DruidClient.execute_query')
    @patch('resources.src.ai.shallow_outliers.ShallowOutliers.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_invalid_b64_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = False
        data = {'model':'model', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('resources.src.druid.client.DruidClient.execute_query')
    @patch('resources.src.ai.outliers.Autoencoder.execute_prediction_model')
    @patch('os.path.isfile')
    def test_calculate_endpoint_valid_model(self, mock_isfile, mock_execute_model, mock_query):
        mock_execute_model.return_value = self.output_data
        mock_query.return_value = {}
        mock_isfile.return_value = True
        data = {'model':'dHJhZmZpYw==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), self.output_data)

    @patch('resources.src.druid.client.DruidClient.execute_query')
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

    def test_post_base64_encoded_data(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(current_dir, "outliers_test_data.json")
        with open(data_file_path, 'r') as file:
            json_data = json.load(file)
        encoded_json = base64.b64encode(json.dumps(json_data).encode('utf-8')).decode('utf-8')
        data = {'model':'dHJhZmZpYw==',  'data': encoded_json}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)

if __name__ == '__main__':
    unittest.main()
