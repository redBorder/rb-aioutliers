# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors:
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
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

import unittest
from unittest.mock import patch, MagicMock
import json
from resources.src.server.rest import config
from resources.src.redborder.rb_ai_outliers_filters import RbAIOutliersFilters

class TestRbAIOutliersFilters(unittest.TestCase):

    @patch('resources.src.config.configmanager.ConfigManager.get')
    @patch('requests.get')
    def test_get_filtered_data_success(self, mock_get, mock_config_get):
        mock_config_get.side_effect = lambda section, key: 'test_endpoint' if key == 'endpoint' else 'test_token'
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'test_model': '{"key": "value"}'
        }
        mock_get.return_value = mock_response
        rb_filters = RbAIOutliersFilters()
        result = rb_filters.get_filtered_data('test_model')
        self.assertEqual(result, {'key': 'value'})

    @patch('resources.src.config.configmanager.ConfigManager.get')
    @patch('requests.get')
    def test_get_filtered_data_exception(self, mock_get, mock_config_get):
        mock_config_get.side_effect = lambda section, key: 'test_endpoint' if key == 'endpoint' else 'test_token'
        mock_get.side_effect = Exception('Test exception')
        rb_filters = RbAIOutliersFilters()
        result = rb_filters.get_filtered_data('test_model')
        self.assertEqual(result, {})

if __name__ == '__main__':
    unittest.main()
