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
from unittest.mock import patch
from io import StringIO

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.Logger.logger import Logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_log_file = './test_log.log'
        self.logger = Logger(log_file=self.temp_log_file, log_level=logging.DEBUG)

    def tearDown(self):
        if os.path.exists(self.temp_log_file):
            os.remove(self.temp_log_file)

    def test_info_logging(self):
        self.logger.info("Test info message")

        with open(self.temp_log_file, 'r') as log_file:
            log_content = log_file.read()

        self.assertTrue("Test info message" in log_content)

    def test_error_logging(self):
        self.logger.error("Test error message")

        with open(self.temp_log_file, 'r') as log_file:
            log_content = log_file.read()

        self.assertTrue("Test error message" in log_content)

    def test_log_level_setting(self):
        self.logger.debug("This is a debug message")

        with open(self.temp_log_file, 'r') as log_file:
            log_content = log_file.read()

        self.assertTrue("This is a debug message" in log_content)

if __name__ == '__main__':
    unittest.main()