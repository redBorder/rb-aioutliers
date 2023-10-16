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

import pytz
import ntplib
from datetime import datetime, timedelta

class NTPClient:
    def __init__(self, server="pool.ntp.org"):
        print(server)
        self.server = server

    def get_ntp_time(self):
        try:
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request(self.server)
            ntp_time = datetime.fromtimestamp(response.tx_time)
            return ntp_time
        except Exception as e:
            return None

    def get_substracted_day_time(self, time=None):
        if time is None:
            time = self.get_ntp_time()
        return time - timedelta(days=1)

    def time_to_iso8601_time(self, time=None):
        if time is None:
            time = self.get_ntp_time()

        return time.strftime("%Y-%m-%dT%H:%M:%SZ")