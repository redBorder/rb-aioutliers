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
from resources.src.server.rest import config

class RbAIOutliersFilters:
    WEBUI_API_ENDPOINT = "/api/v1/filters/get_json"

    def get_filtered_data(self, model_name):
        try:
            endpoint = f"{config.get('rails', 'endpoint')}{self.WEBUI_API_ENDPOINT}/?auth_token{config.get('rails', 'auth_token')}"
            req = requests.get(endpoint, verify=False)
            filters = req.json()
            return filters[model_name]

        except Exception:
            return {}
