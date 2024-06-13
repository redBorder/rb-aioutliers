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
import json
import shutil
from datetime import datetime, timezone, timedelta
from resources.src.redborder.s3 import S3
from resources.src.ai.trainer import Trainer
from resources.src.config.configmanager import ConfigManager
from resources.src.logger.logger import logger
from resources.src.druid.client import DruidClient
from resources.src.druid.query_builder import QueryBuilder
from resources.src.redborder.rb_ai_outliers_filters import RbAIOutliersFilters

class RbOutlierTrainJob:
    def __init__(self, config: ConfigManager) -> None:
        """
        Initialize the Outliers application.

        This class manages the training and running of the Outliers application.

        Args:
            config (ConfigManager): Configuration settings including the ones for the S3 client.
        """
        self.query_builder = None
        self.setup_s3(config)
        self.main_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
        self.druid_client = DruidClient(config.get("Druid", "druid_endpoint"))
        self.training_conf = {
            "epochs": int(config.get("Outliers", "epochs")),
            "batch_size": int(config.get("Outliers", "batch_size")),
            "backup_path": config.get("Outliers", "backup_path")
        }

    def setup_s3(self, config: ConfigManager):
        """
        Set up the S3 client for handling interactions with Amazon S3.

        This function initializes the S3 client with the AWS public key, private key, region, bucket, and hostname as specified in the configuration.

        Args:
            config (ConfigManager): Configuration settings including the ones for the S3 client.
        """
        self.s3_client = S3(
            config.get("AWS", "s3_public_key"),
            config.get("AWS", "s3_private_key"),
            config.get("AWS", "s3_region"),
            config.get("AWS", "s3_bucket"),
            config.get("AWS", "s3_hostname")
        )

    def download_file(self, s3_path: str, local_path, default_local_path):
        """
        Helper function to download a file from S3, falling back to copying a default file locally if necessary.

        Args:
            s3_path (str): The S3 path of the file to download.
            local_path (str): The local path where the file will be saved.
            default_local_path (str): The local path of the default file to copy if the primary file does not exist in S3.
        """
        try:
            if self.s3_client.exists(s3_path):
                self.s3_client.download_file(s3_path, local_path)
                logger.logger.info(f"Downloaded {s3_path} to {local_path}")
            else:
                shutil.copyfile(default_local_path, local_path)
                logger.logger.info(f"File {s3_path} not found in S3. Copied default file from {default_local_path} to {local_path}")
        except Exception as e:
            logger.logger.error(f"Error processing file from S3 or copying default file: {e}")

    def download_model_from_s3(self, model_name):
        """
        Download the latest files associated with a specific model from Amazon S3 and save them to the local AI directory.

        Args:
            model_name (str): The identifier of the model for which the latest file needs to be downloaded.
        """
        extensions = ['keras', 'ini']
        for ext in extensions:
            filename = f"{model_name}.{ext}"
            s3_path = f'rbaioutliers/latest/{filename}'
            local_path = os.path.join(self.main_dir, "ai", filename)
            default_local_path = os.path.join(self.main_dir, "ai", f'traffic.{ext}')
            self.download_file(s3_path, local_path, default_local_path)

    def upload_file(self, local_path, s3_path):
        """
        Helper function to upload a file to an S3 bucket.

        Args:
            local_path (str): The local path of the file to upload.
            s3_path (str): The S3 path where the file will be uploaded.
        """
        try:
            self.s3_client.upload_file(local_path, s3_path)
            logger.logger.info(f"Uploaded {local_path} to {s3_path}")
        except Exception as e:
            logger.logger.error(f"Error uploading file to S3: {e}")

    def upload_model_to_s3(self, model_name):
        """
        Upload the latest files associated with a specific model to Amazon S3.

        Args:
            model_name (str): The identifier of the model for which the latest file needs to be uploaded.
        """
        extensions = ['keras', 'ini']
        for ext in extensions:
            filename = f"{model_name}.{ext}"
            local_path = os.path.join(self.main_dir, "ai", filename)
            s3_path = f'rbaioutliers/latest/{filename}'
            self.upload_file(local_path, s3_path)

    def get_iso_time(self):
        """Returns a string with the current timestamp in ISO format."""
        dt_utc = datetime.now(timezone.utc).replace(microsecond=0)
        return dt_utc.isoformat

    def subtract_one_day(self, iso_time_str):
        """Given a timestamp string in ISO format, returns timestamp of one day before"""
        dt = datetime.fromisoformat(iso_time_str)
        dt_minus_one_day = dt - timedelta(days=1)
        return dt_minus_one_day.isoformat()

    def train_job(self, model_name):
        """
        Start the Outliers training job.

        This function handles the Outliers training process, fetching data, and training the model.
        """
        logger.logger.info("Getting model files from S3")
        self.download_model_from_s3(model_name)
        logger.info("Starting Outliers Train Job")
        traffic_query = self.load_traffic_query()
        self.query_builder = QueryBuilder(
            self.get_aggregation_config_path(),
            self.get_post_aggregations_config_path()
        )
        query = self.query_builder.modify_aggregations(traffic_query)
        self.trainer = Trainer(
            os.path.join(self.main_dir, "ai", f"{model_name}.keras"),
            os.path.join(self.main_dir, "ai", f"{model_name}.ini"),
        )
        self.process_model_data(model_name, query)

    def load_traffic_query(self):
        """
        Load the traffic query.

        Returns:
            dict: The loaded traffic query as a dictionary.
        """
        traffic_json_file_path = os.path.join(self.main_dir, "druid", "data", "trafficquery.json")
        with open(traffic_json_file_path, 'r') as json_file:
            return json.load(json_file)

    def get_aggregation_config_path(self):
        """
        Get the path to the aggregation configuration.

        Returns:
            str: The path to the aggregation configuration file.
        """
        return os.path.join(self.main_dir, "druid", "data", "aggregations.json")

    def get_post_aggregations_config_path(self):
        """
        Get the path to the post-aggregations configuration.

        Returns:
            str: The path to the post-aggregations configuration file.
        """
        return os.path.join(self.main_dir, "druid", "data", "postAggregations.json")

    def process_model_data(self, model_name, query):
        """
        Process data and train the model.

        Args:
            model_name (str): Model identifier.
            query (dict): The query to be modified.

        This function processes data, modifies the query, and trains the model.
        """
        rb_granularities=["pt1m", "pt2m", "pt5m", "pt15m", "pt30m", "pt1h", "pt2h", "pt8h"]
        end_time = self.get_iso_time()
        start_time = self.subtract_one_day(end_time)
        model_filter = RbAIOutliersFilters().get_filtered_data(model_name)
        query = self.query_builder.modify_filter(query, model_filter)
        query = self.query_builder.set_time_origin(query, start_time)
        query = self.query_builder.set_time_interval(query, start_time, end_time)
        traffic_data=[]
        for gran in rb_granularities:
            temp_query = self.query_builder.modify_granularity(query,gran)
            traffic_data.append(self.druid_client.execute_query(temp_query))
        self.trainer.train(
            traffic_data,
            self.training_conf["epochs"],
            self.training_conf["batch_size"],
            self.training_conf["backup_path"]
        )
        self.upload_model_to_s3(model_name)
