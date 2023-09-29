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
import tempfile
import configparser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.config.configmanager import ConfigManager

class TestConfigManager(unittest.TestCase):
    def setUp(self):
        self.temp_config_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_config_file.close()

    def tearDown(self):
        os.remove(self.temp_config_file.name)

    def test_get_existing_option(self):
        config_manager = ConfigManager(self.temp_config_file.name)
        config_manager.set('my_section', 'my_option', 'my_value')
        config_manager.save(self.temp_config_file.name)
        result = config_manager.get('my_section', 'my_option')
        self.assertEqual(result, 'my_value')

    def test_get_nonexistent_option(self):
        config_manager = ConfigManager(self.temp_config_file.name)
        with self.assertRaises((configparser.NoOptionError, configparser.NoSectionError)):
            config_manager.get('nonexistent_section', 'nonexistent_option')

    def test_set_option(self):
        config_manager = ConfigManager(self.temp_config_file.name)
        config_manager.set('my_section', 'my_option', 'my_value')
        config_manager.save(self.temp_config_file.name)
        result = config_manager.get('my_section', 'my_option')
        self.assertEqual(result, 'my_value')

if __name__ == '__main__':
    unittest.main()