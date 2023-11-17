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
    def setUp(self):
        self.api_server = APIServer()

    def tearDown(self):
        pass

    def test_calculate_endpoint_missing_query(self):
        data = {'model':'YXNkZg=='}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json(), {'msg': 'Druid query is empty', 'status':'error'})

    def test_calculate_endpoint_invalid_query(self):
        data = {'model':'YXNkZg==', 'query':'YXNkZg=='}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.get_json(),
                {'msg': 'Invalid query: YXNkZg==', 'status':'error'}
            )

    @patch('druid.client.DruidClient.execute_query')
    @patch('os.path.isfile')
    def test_calculate_endpoint_invalid_model(self, mock_isfile, mock_execute_query):
        mock_isfile.return_value = False
        mock_execute_query.return_value = [
            {"timestamp": "2023-01-01T00:00:00", "result": {"value": 1}},
            {"timestamp": "2023-01-01T01:00:00", "result": {"value": 2}},
            {"timestamp": "2023-01-01T02:00:00", "result": {"value": 3}},
            {"timestamp": "2023-01-01T03:00:00", "result": {"value": 4}},
        ]
        data = {'model':'YXNkZg==', 'query':'eyJhc2RmIjoiYXNkZiJ9'}
        with self.api_server.app.test_client().post('/api/v1/outliers', data=data) as response:
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.get_json()["status"], "success")

if __name__ == '__main__':
    unittest.main()
