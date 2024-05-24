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


import requests
import json

class DruidClient:
    def __init__(self, druid_endpoint):
        """
        Initialize a DruidClient instance with the specified Druid endpoint.

        Args:
            druid_endpoint (str): The URL of the Druid endpoint.
        """
        self.druid_endpoint = druid_endpoint

    def execute_query(self, druid_query):
        """
        Execute a Druid query using the specified query dictionary.

        Args:
            druid_query (dict): The Druid query in dictionary format.

        Returns:
            dict: The response from the Druid query in JSON format.

        Raises:
            Exception: If the Druid query fails with a non-200 status code.
        """
        query_json = json.dumps(druid_query)
        response = requests.post(self.druid_endpoint, data=query_json)

        if response.status_code == 200:
            response_json = response.json()
            return response_json

        raise Exception(f"Druid query failed with status code {response.status_code}.")
