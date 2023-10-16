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
        return RedBorderAPI(config.get("redBorder", "api_endpoint"), config.get("redBorder", "api_oauth_token"))

    def initialize_ntp_client(self):
        return NTPClient(config.get("NTP", "ntp_server"))

    def initialize_druid_client(self):
        return DruidClient(config.get("Druid", "druid_endpoint"))

    def load_traffic_query(self):
        traffic_json_file_path = os.path.join(os.path.dirname(__file__), "druid", "data", "trafficquery.json")
        with open(traffic_json_file_path, 'r') as json_file:
            return json.load(json_file)

    def get_aggregation_config_path(self):
        return os.path.join(os.path.dirname(__file__), "druid", "data", "aggregations.json")

    def get_post_aggregations_config_path(self):
        return os.path.join(os.path.dirname(__file__), "druid", "data", "postAggregations.json")

    def process_sensor_data(self, sensor, query, redborder_ntp, manager_time, druid_client):
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
        self.api = APIServer()
        self.api.start_test_server(test_run_github_action)

    def run_production_server(self):
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