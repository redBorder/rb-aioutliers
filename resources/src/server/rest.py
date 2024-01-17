# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
# Miguel Álvarez Adsuara <malvarez@redborder.com>
# Pablo Rodriguez Flores <prodriguez@redborder.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 2 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


import os
import sys
import json
import time
import base64
import threading
from flask import Flask, jsonify, request

from resources.src.redborder.s3 import S3
from resources.src.ai import outliers, shallow_outliers
from resources.src.druid import client, query_builder
from resources.src.logger import logger
from resources.src.config import configmanager


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
        self.ai_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ai")

        @self.app.route('/api/v1/outliers', methods=['POST'])
        def calculate():
            """
            Handle POST requests to '/api/v1/outliers'.
            The endpoint expects parameters either in the request body or as form parameters with
            the following format:
            {
                "query": "<base64_encoded_json_druid_query>",
                "model": "<base64_encoded_model_name>"  # Optional field
            }

            Where:
            - `query`: A base64 encoded JSON Druid query specifying the data for analysis.
            - `model` (Optional): A base64 encoded string representing the path of the predictive
            model to be used. If not provided or if the specified model is not found, a default
            model is used.

            Returns:
                A JSON response containing the prediction results or an error message.
            """

            druid_query = request.form.get('query')
            try:
                druid_query = base64.b64decode(druid_query).decode('utf-8')
                druid_query = json.loads(druid_query)
            except Exception as e:
                error_message = "Error decoding query"
                logger.logger.error(error_message + " -> " + str(e))
                return self.return_error(error=error_message)
            logger.logger.info("Druid query successfully decoded and loaded as JSON.")

            model = request.form.get('model')
            if model is None:
                logger.logger.info("No model requested")
                model = 'default'
            else:
                try:
                    decoded_model = base64.b64decode(model).decode('utf-8')
                    model_path = os.path.normpath(os.path.join(self.ai_path, f"{decoded_model}.keras"))
                    if not model_path.startswith(os.path.normpath(self.ai_path)):
                        logger.logger.error(f"Attempted unauthorized file access: {decoded_model}")
                        model = 'default'
                    elif not os.path.isfile(model_path):
                        logger.logger.error(f"Model {decoded_model} does not exist")
                        model = 'default'
                    else:
                        model = decoded_model
                except Exception as e:
                    logger.logger.error(f"Error decoding or checking model -> {e}")
                    model = 'default'
            return self.execute_model(druid_query, config.get("Outliers","metric"), model)

    def execute_model(self, druid_query, metric, model='default'):
        """
        Execute a keras deep learning model to detect outliers.

        Args:
            druid_query (dict): druid query for the data that we want to analyze.
            metric (string): the name of field being analyzed.
            model (string): the name of the model we want to use.

        Returns:
            (JSON): json containing the model's predictions and the outliers detected.
        """

        if model != 'default':
            logger.logger.info(f"Calculating predictions with keras model {model}.keras")
            druid_query = query_modifier.modify_aggregations(druid_query)
        else:
            logger.logger.info("Calculating predictions with default model")
        data = druid_client.execute_query(druid_query)
        try:
            if model != 'default':
                return jsonify(outliers.Autoencoder.execute_prediction_model(
                    data,
                    metric,
                    os.path.join(self.ai_path, f"{model}.keras"),
                    os.path.join(self.ai_path, f"{model}.ini")
                ))
            return jsonify(shallow_outliers.ShallowOutliers.execute_prediction_model(data))
        except Exception as e:
            error_message = "Error while calculating prediction model"
            logger.logger.error(error_message + " -> " + str(e))
            return self.return_error(error=error_message)

    def return_error(self, error="error"):
        """
        Returns an adequate formatted JSON for whenever there is an error.

        Args:
            error (string): message detailing what type of error has been fired.
        """
        return jsonify({ "status": "error", "msg":error })

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
            self.app.run(
                debug=False,
                host=config.get("OutliersServerTesting", "outliers_binding_address"),
                port=config.get("OutliersServerTesting", "outliers_server_port")
            )
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
