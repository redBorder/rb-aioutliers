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

import os, sys
import unittest
from unittest.mock import Mock, patch
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.redborder.async_jobs.train_job import RbOutlierTrainJob 

class TestRbOutlierTrainJob(unittest.TestCase):
    
    def setUp(self):
        self.mock_S3 = patch('src.redborder.async_jobs.train_job.S3').start()
        self.mock_config = patch('src.redborder.async_jobs.train_job.config').start()

        self.mock_config.get.return_value = 0

    def tearDown(self):
        patch.stopall()

    def test_setup_s3(self):
        job = RbOutlierTrainJob()
        job.setup_s3()
        self.mock_S3.assert_called_with(0,0,0,0,0)


if __name__ == '__main__':
    unittest.main()