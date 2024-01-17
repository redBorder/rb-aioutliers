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
import logging
import unittest
from io import StringIO
from unittest.mock import Mock, patch
from tempfile import TemporaryDirectory

from resources.src.logger.logger import Logger

class TestLogger(unittest.TestCase):
    def setUp(self):
        self.temp_log_file = './test_log.log'
        self.logger = Logger(log_file=self.temp_log_file, log_level=logging.DEBUG)
        self.temp_dir = TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

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


    def test_invalid_config_manager(self,):
        log_file=self.logger.get_log_file('./invalid_config.ini')
        self.assertEqual(log_file, "./outliers.log")

    def test_create_log_directory(self):
        log_dir = os.path.join(self.temp_dir.name, 'log_directory')
        logger = Logger(log_file=os.path.join(log_dir, 'test.log'))
        self.assertTrue(os.path.exists(log_dir))
        self.assertTrue(os.path.isdir(log_dir))
        self.assertTrue(os.path.exists(os.path.join(log_dir, 'test.log')))

if __name__ == '__main__':
    unittest.main()