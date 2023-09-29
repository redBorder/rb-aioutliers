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

import os
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.redborder import client

class TestRedBorderAPI(unittest.TestCase):
    def setUp(self):
        self.mock_response = Mock()
        self.mock_response.status_code = 200
        self.mock_response.json.return_value = {'flow': 'mocked_data'}

    def test_request_flow_sensors_success(self):
        api = client.RedBorderAPI(endpoint='http://mocked-endpoint', oauth_token='mocked-token')

        with unittest.mock.patch('requests.get', return_value=self.mock_response):
            result = api.request_flow_sensors()

        self.assertEqual(result, 'mocked_data')

    def test_request_flow_sensors_failure(self):
        api = client.RedBorderAPI(endpoint='http://mocked-endpoint', oauth_token='mocked-token')

        self.mock_response.status_code = 404
        with unittest.mock.patch('requests.get', return_value=self.mock_response):
            with self.assertRaises(Exception) as context:
                api.request_flow_sensors()

        self.assertIn("redBorder api request failed with status code 404.", str(context.exception))

if __name__ == '__main__':
    unittest.main()