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


import os, sys
import unittest
from rq import Queue
from unittest.mock import Mock, patch, create_autospec
from datetime import datetime, timedelta
from croniter import croniter

from resources.src.redborder.rq import RqManager
from resources.src.redborder.async_jobs.train_job import RbOutlierTrainJob

class TestRqManager(unittest.TestCase):
    def setUp(self):
        self.rq_manager = RqManager()

    def tearDown(self):
        self.rq_manager = None

    @patch('resources.src.redborder.rq.Redis')
    @patch('resources.src.redborder.rq.config')
    def test_init(self, mock_config, mock_redis):
        mock_config.get.return_value = 0
        mock_redis.return_value = Mock()
        rq_manager = RqManager()

        self.assertIsInstance(rq_manager.rq_queue, Queue)
        mock_redis.assert_called_with(host=0, port=0, password=0)

    @patch('resources.src.redborder.rq.config')
    def test_fetch_queue_default_job_hour(self, mock_config):
        mock_config.get.return_value = "30 3 * * *"
        cron_syntax = self.rq_manager.fetch_queue_default_job_hour()
        self.assertEqual(cron_syntax, "30 3 * * *")

    @patch('resources.src.redborder.rq.config')
    def test_fetch_redis_hostname(self, mock_config):
        mock_config.get.return_value = "localhost"
        redis_hostname = self.rq_manager.fetch_redis_hostname()
        self.assertEqual(redis_hostname, "localhost")

    @patch('resources.src.redborder.rq.config')
    def test_fetch_redis_port(self, mock_config):
        mock_config.get.return_value = 16379
        redis_port = self.rq_manager.fetch_redis_port()
        self.assertEqual(redis_port, 16379)

    @patch('resources.src.redborder.rq.config')
    def test_fetch_redis_secret(self, mock_config):
        mock_config.get.return_value = "your_redis_secret"
        redis_secret = self.rq_manager.fetch_redis_secret()
        self.assertEqual(redis_secret, "your_redis_secret")

    @patch('resources.src.redborder.rq.config')
    def test_fetch_model_names(self, mock_config):
        mock_config.get.return_value = "model1,model2,model3"
        model_names = self.rq_manager.fetch_model_names()
        self.assertEqual(model_names, "model1,model2,model3")

    def test_cron_to_rq_datetime(self):
        cron_expression = "30 3 * * *"
        current_date = datetime.now()
        expected_datetime = current_date+timedelta(days=1)
        expected_datetime = expected_datetime.replace(hour=3,minute=30,second=0,microsecond=0)
        result_datetime = self.rq_manager.cron_to_rq_datetime(cron_expression)
        self.assertEqual(result_datetime, expected_datetime)

if __name__ == '__main__':
    unittest.main()
