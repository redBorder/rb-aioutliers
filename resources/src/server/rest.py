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
import json
import base64
from IA import outliers
from Druid import client
from Logger import logger
from Config import configmanager
from flask import Flask, jsonify, request

'''
Init local variables
'''

config = configmanager.ConfigManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"))
druid_client = client.DruidClient(config.get("Druid", "druid_endpoint"))

class APIServer:
    def __init__(self):
        self.app = Flask(__name__)

        @self.app.route('/api/v1/outliers', methods=['POST'])
        def calculate():
            logger.logger.info("Calculating predictions with Keras model")
            if request.form.get('query') != None:
                
                druid_query = json.loads(base64.b64decode(request.form.get('query')).decode('utf-8'))
                druid_query['aggregations'] = [ { "type": "longSum", "name": "bytes", "fieldName": "sum_bytes" }, { "type": "longSum", "name": "pkts", "fieldName": "sum_pkts" }, { "type": "hyperUnique", "name": "clients", "fieldName": "clients" }, { "type": "longSum", "name": "flows", "fieldName": "events" } ]
                data = druid_client.execute_query(druid_query)
                logger.logger.info("Returning predicted data")
                print(druid_query)
                try:
                    return jsonify(outliers.OutliersModel.execute_prediction_model(
                        data,
                        config.get("OutliersServer", "metric"),
                        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "IA", "autoencoder.keras")
                    ))	
                except Exception as e:
                    logger.logger.error("Error while calculating prediction model -> " + str(e))
                    return jsonify(outliers.OutliersModel.return_error(error=str(e)))
            else:
                logger.logger.error("Error while proccessing, Druid query is empty")
                return jsonify(outliers.OutliersModel.return_error())
    
    def start_server(self, test):
        if test:
            return
        else:
            self.app.run(debug=False, host="0.0.0.0", port=config.get("OutliersServer", "outliers_server_port"))