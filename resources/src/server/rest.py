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
import sys
import json
import time
import base64
import threading
from redborder.s3 import S3
from ai import outliers
from druid import client, query_builder
from logger import logger
from config import configmanager
from flask import Flask, jsonify, request

'''
Init local variables
'''

config = configmanager.ConfigManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"))
druid_client = client.DruidClient(config.get("Druid", "druid_endpoint"))
query_modifier = query_builder.QueryBuilder(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "druid", "data", "aggregations.json"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "druid", "data", "postAggregations.json")
)

class APIServer:
    def __init__(self):
        """
        Initialize the API server.

        This class uses Flask to create a web API for processing requests.
        """

        self.s3_client = S3(
            config.get("AWS", "s3_public_key"),
            config.get("AWS", "s3_private_key"),
            config.get("AWS", "s3_region"),
            config.get("AWS", "s3_bucket"),
            config.get("AWS", "s3_hostname")
        )

        self.s3_sync_interval = 60
        self.s3_sync_thread = None
        self.start_s3_sync_thread()

        self.app = Flask(__name__)
        self.exit_code = 0

        @self.app.route('/api/v1/outliers', methods=['POST'])
        def calculate():
            """
            Handle POST requests to '/api/v1/outliers'.

            This function processes requests by performing data manipulation and prediction.

            Returns:
                JSON response containing prediction results or an error message.
            """
            logger.logger.info("Calculating predictions with Keras model")
            if request.form.get('query') is not None:
                druid_query = json.loads(base64.b64decode(request.form.get('query')).decode('utf-8'))
                druid_query = query_modifier.modify_aggregations(druid_query)
                data = druid_client.execute_query(druid_query)
                flow_sensor = druid_query["filter"]["value"]
                try:
                    return jsonify(outliers.Autoencoder.execute_prediction_model(
                        data,
                        config.get("Outliers", "metric"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai", f"{flow_sensor}.keras"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai", f"{flow_sensor}.ini")
                    ))
                except Exception as e:
                    logger.logger.error("Error while calculating prediction model -> " + str(e))
                    return jsonify(outliers.Autoencoder.return_error(error=str(e))
                )
            else:
                logger.logger.error("Error while processing, Druid query is empty")
                return jsonify(outliers.Autoencoder.return_error())

    def start_s3_sync_thread(self):
        """
        Start a thread for syncing with S3 at regular intervals.
        """
        self.s3_sync_thread = threading.Thread(target=self.sync_with_s3_periodically)
        self.s3_sync_thread.daemon = True
        self.s3_sync_thread.start()

    def sync_with_s3_periodically(self):
        """
        Periodically sync with Amazon S3.
        """
        while True:
            logger.logger.info("Sync with S3 Started")
            self.sync_models_with_s3()
            logger.logger.info("Sync with S3 Finished")
            time.sleep(self.s3_sync_interval)

    def sync_models_with_s3(self):
        """
        Synchronize models with Amazon S3.

        This function retrieves a list of objects in the 'rbaioutliers/latest' folder on Amazon S3 using the S3 client.
        It then iterates through the list, extracts the file name, and downloads each object to the local 'ai' directory.
        """
        objects = self.s3_client.list_objects_in_folder('rbaioutliers/latest')
        for obj in objects:
            file_name = obj.split("/")[-1]
            self.s3_client.download_file(obj, os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai"), file_name))

    def run_test_app(self):
        """
        Run the test server.

        This function starts the Flask app to serve requests.

        In case of an exception, it logs the error and sets the exit code to 1.
        """
        try:
            self.app.run(debug=False, host=config.get("OutliersServerTesting", "outliers_binding_address"), port=config.get("OutliersServerTesting", "outliers_server_port"))
        except Exception as e:
            logger.logger.error(f"Exception in server thread: {e}")
            self.exit_code = 1

    def start_test_server(self, test_run_github_action):
        """
        Start the test server.

        Args:
            test_run_github_action (bool): Indicates whether this is a test run in a GitHub action.
        """
        if test_run_github_action:
            self.server_thread = threading.Thread(target=self.run_test_app)
            self.server_thread.daemon = True
            self.server_thread.start()
            time.sleep(30)
            sys.exit(self.exit_code)
        else:
            self.run_test_app()