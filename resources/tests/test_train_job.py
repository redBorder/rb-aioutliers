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


import os
import sys
import unittest
from unittest.mock import Mock, patch, call
from datetime import datetime, timezone, timedelta

from resources.src.redborder.s3 import S3
from resources.src.config.configmanager import ConfigManager
from resources.src.redborder.async_jobs.train_job import RbOutlierTrainJob
from resources.src.druid.client import DruidClient
from resources.src.ai.trainer import Trainer
from resources.src.logger.logger import logger

config_path = "resources/tests/config_test.ini"
config = ConfigManager(config_path)

class TestRbOutlierTrainJob(unittest.TestCase):

    def setUp(self):
        self.train_job = RbOutlierTrainJob(config)

    def tearDown(self):
        pass

    def test_setup_s3(self):
        self.assertIsInstance(self.train_job.s3_client, S3)

    @patch('shutil.copyfile')
    @patch.object(S3, 'download_file')
    @patch.object(S3, 'exists', return_value=True)
    def test_download_file_exists(self, mock_exists, mock_download_file, mock_copyfile):
        s3_path = 's3_path'
        local_path = 'local_path'
        default_local_path = 'default_local_path'

        self.train_job.download_file(s3_path, local_path, default_local_path)

        mock_exists.assert_called_once_with(s3_path)
        mock_download_file.assert_called_once_with(s3_path, local_path)
        mock_copyfile.assert_not_called()

    @patch('shutil.copyfile')
    @patch.object(S3, 'download_file')
    @patch.object(S3, 'exists', return_value=False)
    def test_download_file_not_exists(self, mock_exists, mock_download_file, mock_copyfile):
        s3_path = 's3_path'
        local_path = 'local_path'
        default_local_path = 'default_local_path'

        self.train_job.download_file(s3_path, local_path, default_local_path)

        mock_exists.assert_called_once_with(s3_path)
        mock_download_file.assert_not_called()
        mock_copyfile.assert_called_once_with(default_local_path, local_path)

    @patch.object(S3, 'upload_file')
    def test_upload_file(self, mock_upload_file):
        local_path = 'local_path'
        s3_path = 's3_path'

        self.train_job.upload_file(local_path, s3_path)

        mock_upload_file.assert_called_once_with(local_path, s3_path)

    def test_get_iso_time(self):
        iso_time = self.train_job.get_iso_time()
        expected_time = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        self.assertEqual(iso_time(), expected_time)

    def test_subtract_one_day(self):
        iso_time_str = '2023-01-01T00:00:00+00:00'
        expected_time_str = '2022-12-31T00:00:00+00:00'
        result_time_str = self.train_job.subtract_one_day(iso_time_str)
        self.assertEqual(result_time_str, expected_time_str)

if __name__ == '__main__':
    unittest.main()
