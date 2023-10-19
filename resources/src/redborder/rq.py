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

import sys, os, time
from rq import Queue
from redis import Redis
from datetime import datetime
from croniter import croniter
try:
    from server.rest import config
    from logger.logger import logger
    from redborder.async_jobs.train_job import RbOutlierTrainJob
except:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
    from src.server.rest import config
    from src.logger.logger import logger
    from src.redborder.async_jobs.train_job import RbOutlierTrainJob

class RqManager:
    def __init__(self) -> None:
        """
        Initialize the RqManager module.

        This class manages the job service across all redborder cluster running this service
        """
        self.rq_queue = Queue(connection=Redis(host=self.fetch_redis_hostname(), port=self.fetch_redis_port(), password=self.fetch_redis_secret()))

    def fetch_queue_default_job_hour(self):
        """
        Fetch queue cron syntax from config file
        Returns:
            str: cron syntax
        """
        return config.get("Outliers", "schedule_hour")

    def fetch_redis_hostname(self):
        """
        Fetch redis hostname from config file
        Returns:
            str: redis hostname
        """
        return config.get("Redis", "rd_hostname")

    def fetch_redis_port(self):
        """
        Fetch redis hostname from config file
        Returns:
            str: redis hostname
        """
        return int(config.get("Redis", "rd_port"))

    def fetch_redis_secret(self):
        """
        Fetch redis secret from config file
        Returns:
            str: redis secret
        """
        return config.get("Redis", "rd_secret")

    def fetch_flow_sensors(self):
        """
        Fetch flow sensors from the config file
        Returns:
            str: flow sensors
        """
        return config.get("Outliers", "target_sensors")

    def cron_to_rq_datetime(self, cron_expression):
        """
        Convert a cron expression to a valid datetime object for the next scheduled time.

        Args:
            cron_expression (str): Cron expression in the format "min hour day month day_of_week".

        Returns:
            datetime: A valid datetime object representing the next scheduled time.
        """
        parts = cron_expression.strip().split()
        if len(parts) != 5:
            raise ValueError("Invalid cron expression. It should have 5 fields.")

        minute, hour, day_of_month, month, day_of_week = parts

        cron_str = f"{minute} {hour} {day_of_month} {month} {day_of_week}"

        cron = croniter(cron_str, datetime.now())
        next_run = cron.get_next(datetime)

        return next_run

    def schedule_train_job(self):
        """
        Schedule the training job to run periodically based on a cron expression.

        This function enqueue jobs across the redborder cluster for distributed processing

        """
        logger.info("Re-queue train job")
        outlier_job = RbOutlierTrainJob()
        crontime = self.fetch_queue_default_job_hour()
        cron_schedule = self.cron_to_rq_datetime(crontime)

        while True:
            current_time = time.time()
            next_execution_time = cron_schedule.timestamp()
            delay = max(0, next_execution_time - current_time)

            if delay > 0:
                logger.info("Waiting for re-queue...")
                time.sleep(delay)
                self.schedule_train_job()

