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

import schedule
import os, json, time
from ntp.ntp import NTPClient
from ai.trainer import Trainer
from logger.logger import logger
from druid.client import DruidClient
from server.rest import APIServer, config
from server.production import GunicornApp
from redborder.client import RedBorderAPI
from druid.query_builder import QueryBuilder

class Outliers:
    def __init__(self) -> None:
        """
        Initialize the Outliers application.

        This class manages the training and running of the Outliers application.
        """
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self.server = None
        self.app = None
        self.query_builder = None
        self.trainer = Trainer(
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "traffic.keras"),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "ai", "traffic.ini"),
        )
        self.run()

    def train_job(self):
        """
        Start the Outliers training job.

        This function handles the Outliers training process, fetching data, and training the model.
        """
        logger.info("Starting Outliers Train Job")

        redborder_client = self.initialize_redborder_client()
        redborder_ntp = self.initialize_ntp_client()
        druid_client = self.initialize_druid_client()

        flow_sensors = redborder_client.request_flow_sensors()
        manager_time = redborder_ntp.get_ntp_time()

        traffic_query = self.load_traffic_query()

        self.query_builder = QueryBuilder(self.get_aggregation_config_path(), self.get_post_aggregations_config_path())
        query = self.query_builder.modify_aggregations(traffic_query)

        for sensor in flow_sensors:
            self.process_sensor_data(sensor, query, redborder_ntp, manager_time, druid_client)

    def initialize_redborder_client(self):
        """
        Initialize the RedBorder API client.

        Returns:
            RedBorderAPI: The initialized RedBorder API client.
        """
        return RedBorderAPI(config.get("redBorder", "api_endpoint"), config.get("redBorder", "api_oauth_token"))

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
        traffic_json_file_path = os.path.join(os.path.dirname(__file__), "druid", "data", "trafficquery.json")
        with open(traffic_json_file_path, 'r') as json_file:
            return json.load(json_file)

    def get_aggregation_config_path(self):
        """
        Get the path to the aggregation configuration.

        Returns:
            str: The path to the aggregation configuration file.
        """
        return os.path.join(os.path.dirname(__file__), "druid", "data", "aggregations.json")

    def get_post_aggregations_config_path(self):
        """
        Get the path to the post-aggregations configuration.

        Returns:
            str: The path to the post-aggregations configuration file.
        """
        return os.path.join(os.path.dirname(__file__), "druid", "data", "postAggregations.json")

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
        sensor_name = sensor['name']
        start_time = redborder_ntp.time_to_iso8601_time(redborder_ntp.get_substracted_day_time(manager_time))
        end_time = redborder_ntp.time_to_iso8601_time(manager_time)

        query = self.query_builder.modify_flow_sensor(query, sensor_name)
        query = self.query_builder.set_time_origin(query, start_time)
        query = self.query_builder.set_time_interval(query, start_time, end_time)
        traffic_data = druid_client.execute_query(query)
        self.trainer.train(
            traffic_data,
            int(config.get("Outliers", "epochs")),
            int(config.get("Outliers", "batch_size")),
            config.get("Outliers", "backup_path")
        )

    def run(self):
        """
        Run the application based on the environment.

        This function determines the environment and runs the application accordingly.
        """
        if "production" in self.environment:
            self.run_production_server()
        if "development" in self.environment:
            self.run_test_server(False)
        if "train" in self.environment:
            hours = config.get("Outliers", "schedule_hour")
            schedule.every().day.at(f"{hours}:00").do(self.train_job)
            while True:
                schedule.run_pending()
                time.sleep(1)
        if "test" in self.environment:
            self.run_test_server(True)

    def run_test_server(self, test_run_github_action):
        """
        Run the test server for API testing.

        Args:
            test_run_github_action (bool): Indicates whether this is a test run in a GitHub action.
        """
        self.api = APIServer()
        self.api.start_test_server(test_run_github_action)

    def run_production_server(self):
        """
        Run the production server.

        This function runs the production server using Gunicorn.
        """
        logger.info("Starting Outliers API REST")
        __binding_host__ = config.get("OutliersServerProduction", "outliers_binding_address")
        __binding_port__ = config.get("OutliersServerProduction", "outliers_server_port")
        gunicorn_workers = config.get("OutliersServerProduction", "outliers_server_workers")
        options = {
            'bind': f"{__binding_host__}:{__binding_port__}",
            'workers': gunicorn_workers
        }
        self.server = APIServer()
        self.app = GunicornApp(self.server, options)
        self.app.run()

_Outliers = Outliers()