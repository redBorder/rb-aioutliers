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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from resources.src.logger.logger import logger
from resources.src.server.rest import APIServer, config
from resources.src.server.production import GunicornApp
from resources.src.redborder.zookeeper.rb_outliers_zoo_sync import RbOutliersZooSync

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
        self.run()

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
            self.zoo_sync = RbOutliersZooSync(config)
            self.zoo_sync.sync_nodes()
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
        gunicorn_threads = config.get("OutliersServerProduction", "outliers_server_threads")
        options = {
            'bind': f"{__binding_host__}:{__binding_port__}",
            'workers': gunicorn_workers,
            'threads': gunicorn_threads,
            'worker_class': 'gthread',
            'max_requests': 100,
            'max_worker_lifetime': 3600
        }
        self.server = APIServer()
        self.app = GunicornApp(self.server, options)
        self.app.run()

_Outliers = Outliers()