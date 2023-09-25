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
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.Druid.client import DruidClient

class TestDruidClient(unittest.TestCase):
    def setUp(self):
        self.druid_endpoint = "http://mock.druid.endpoint"
        self.druid_client = DruidClient(self.druid_endpoint)

    def test_execute_query_success(self):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "mocked_data"}

        with patch("requests.post", return_value=mock_response):
            druid_query = {"query": "sample_query"}

            response = self.druid_client.execute_query(druid_query)

            self.assertEqual(response, {"result": "mocked_data"})

    def test_execute_query_failure(self):
        mock_response = MagicMock()
        mock_response.status_code = 500

        with patch("requests.post", return_value=mock_response):
            druid_query = {"query": "sample_query"}

            with self.assertRaises(Exception) as context:
                self.druid_client.execute_query(druid_query)

            self.assertIn("status code 500", str(context.exception))

if __name__ == '__main__':
    unittest.main()
