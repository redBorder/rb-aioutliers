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

import sys, os, json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from rbntp.ntplib import NTPClient
from ai.trainer import Trainer
from logger.logger import logger
from druid.client import DruidClient
from server.rest import config
from druid.query_builder import QueryBuilder
from redborder.s3 import S3

class RbOutlierTrainJob:
    def __init__(self) -> None:
        """
        Initialize the Outliers application.

        This class manages the training and running of the Outliers application.
        """
        self.flow_sensors = None
        self.query_builder = None
        self.s3_client = None

    def setup_s3(self):
        """
        Set up the S3 client for handling interactions with Amazon S3.

        This function initializes the S3 client with the AWS public key, private key, region, bucket, and hostname as specified in the configuration.
        """
        self.s3_client = S3(
            config.get("AWS", "s3_public_key"),
            config.get("AWS", "s3_private_key"),
            config.get("AWS", "s3_region"),
            config.get("AWS", "s3_bucket"),
            config.get("AWS", "s3_hostname")
        )

    def setup_remote_model_sync(self):
        """
        Set up remote model synchronization for flow sensors.

        This function iterates through a list of flow sensors and calls functions to download the latest model
        configuration and model files from Amazon S3 for each flow sensor.
        """
        for flow_sensor in self.flow_sensors:
            self.download_latest_model_config_from_s3(flow_sensor)
            self.download_latest_model_from_s3(flow_sensor)

    def download_latest_model_config_from_s3(self, flow_sensor):
        """
        Download the latest model configuration file associated with a specific flow sensor from Amazon S3 and save it to the local AI directory.

        Args:
            flow_sensor (str): The identifier or name of the flow sensor for which the latest model configuration file needs to be downloaded.
        """
        self.s3_client.download_file(f'rbaioutliers/latest/{flow_sensor}.ini', os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{flow_sensor}.ini"))

    def download_latest_model_from_s3(self, flow_sensor):
        """
        Download the latest model file associated with a specific flow sensor from Amazon S3 and save it to the local AI directory.

        Args:
            flow_sensor (str): The identifier or name of the flow sensor for which the latest model file needs to be downloaded.
        """
        self.s3_client.download_file(f'rbaioutliers/latest/{flow_sensor}.keras', os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{flow_sensor}.keras"))

    def train_job(self, flow_sensors):
        """
        Start the Outliers training job.

        This function handles the Outliers training process, fetching data, and training the model.
        """
        self.setup_s3()
        logger.info("Starting Outliers Train Job")
        redborder_ntp = self.initialize_ntp_client()
        druid_client = self.initialize_druid_client()

        manager_time = redborder_ntp.get_ntp_time()

        traffic_query = self.load_traffic_query()

        self.query_builder = QueryBuilder(self.get_aggregation_config_path(), self.get_post_aggregations_config_path())
        query = self.query_builder.modify_aggregations(traffic_query)

        self.flow_sensors = flow_sensors.join(flow_sensors.split()).split(',')
        self.setup_remote_model_sync()

        for sensor in self.flow_sensors:
            self.trainer = Trainer(
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{sensor}.keras"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{sensor}.ini"),
            )
            self.process_sensor_data(sensor, query, redborder_ntp, manager_time, druid_client)

    def initialize_ntp_client(self):
        """
        Initialize the NTP client.

        Returns:
            NTPClient: The initialized NTP client.
        """
        return NTPClient(config.get("NTP", "ntp_server"))

    def initialize_druid_client(self):
        """
        Initialize the Druid client.

        Returns:
            DruidClient: The initialized Druid client.
        """
        return DruidClient(config.get("Druid", "druid_endpoint"))

    def load_traffic_query(self):
        """
        Load the traffic query.

        Returns:
            dict: The loaded traffic query as a dictionary.
        """
        traffic_json_file_path = os.path.join(os.path.dirname(__file__), "..", "..", "druid", "data", "trafficquery.json")
        with open(traffic_json_file_path, 'r') as json_file:
            return json.load(json_file)

    def get_aggregation_config_path(self):
        """
        Get the path to the aggregation configuration.

        Returns:
            str: The path to the aggregation configuration file.
        """
        return os.path.join(os.path.dirname(__file__), "..", "..", "druid", "data", "aggregations.json")

    def get_post_aggregations_config_path(self):
        """
        Get the path to the post-aggregations configuration.

        Returns:
            str: The path to the post-aggregations configuration file.
        """
        return os.path.join(os.path.dirname(__file__), "..", "..", "druid", "data", "postAggregations.json")

    def upload_model_results_back_to_s3(self, sensor):
        """
        Upload a model file associated with a specific sensor to an Amazon S3 bucket.

        Args:
            sensor (str): The sensor identifier or name for which the model file needs to be uploaded to S3.
        """
        self.s3_client.upload_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{sensor}.keras"),
            f'rbaioutliers/latest/{sensor}.keras'
        )

    def upload_model_config_results_back_to_s3(self, sensor):
        """
        Upload a model configuration file associated with a specific sensor to an Amazon S3 bucket.

        Args:
            sensor (str): The sensor identifier or name for which the model configuration file needs to be uploaded to S3.
        """
        self.s3_client.upload_file(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "ai", f"{sensor}.ini"),
            f'rbaioutliers/latest/{sensor}.ini'
        )

    def upload_results_back_to_s3(self):
        """
        Upload results for all flow sensors to an Amazon S3 bucket.

        This function iterates through a list of flow sensors and uploads both the model file and model configuration
        file for each sensor to the 'rbaioutliers/latest' path in the S3 bucket.
        """
        for sensor in self.flow_sensors:
            self.upload_model_results_back_to_s3(sensor)
            self.upload_model_config_results_back_to_s3(sensor)

    def process_sensor_data(self, sensor, query, redborder_ntp, manager_time, druid_client):
        """
        Process sensor data and train the model.

        Args:
            sensor (dict): Sensor information.
            query (dict): The query to be modified.
            redborder_ntp (NTPClient): The NTP client.
            manager_time (datetime): The manager time.
            druid_client (DruidClient): The Druid client.

        This function processes sensor data, modifies the query, and trains the model.
        """
        start_time = redborder_ntp.time_to_iso8601_time(redborder_ntp.get_substracted_day_time(manager_time))
        end_time = redborder_ntp.time_to_iso8601_time(manager_time)

        query = self.query_builder.modify_flow_sensor(query, sensor)
        query = self.query_builder.set_time_origin(query, start_time)
        query = self.query_builder.set_time_interval(query, start_time, end_time)
        traffic_data = druid_client.execute_query(query)
        self.trainer.train(
            traffic_data,
            int(config.get("Outliers", "epochs")),
            int(config.get("Outliers", "batch_size")),
            config.get("Outliers", "backup_path")
        )
        self.upload_results_back_to_s3()