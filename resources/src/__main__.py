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

import os
from logger.logger import logger
from server.rest import APIServer, config
from server.production import GunicornApp

class Outliers:
    def __init__(self) -> None:
        self.environment = os.environ.get("ENVIRONMENT", "development")
        self.server = None
        self.app = None
        self.run()

    def run(self):
        if "production" in self.environment:
            self.run_production_server()
        if "development" in self.environment:
            self.run_test_server(False)
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