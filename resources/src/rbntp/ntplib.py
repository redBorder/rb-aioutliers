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


import pytz
import ntplib
from datetime import datetime, timedelta

class NTPClient:
    def __init__(self, server="pool.ntp.org"):
        """
        Initialize an NTP client with the specified NTP server.

        Args:
            server (str, optional): The NTP server to use (default is "pool.ntp.org").
        """
        self.server = server

    def get_ntp_time(self):
        """
        Get the current time from the NTP server.

        Returns:
            datetime: The current time obtained from the NTP server.

        If an exception occurs during the NTP request, None is returned.
        """
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(self.server)
        ntp_time = datetime.fromtimestamp(response.tx_time)
        return ntp_time

    def get_substracted_day_time(self, time=None):
        """
        Get the time with one day subtracted from the given time or the current NTP time.

        Args:
            time (datetime, optional): The time to subtract one day from (default is None, which uses the current NTP time).

        Returns:
            datetime: The time with one day subtracted.
        """
        if time is None:
            time = self.get_ntp_time()
        return time - timedelta(days=1)

    def time_to_iso8601_time(self, time=None):
        """
        Convert the given time to ISO 8601 format.

        Args:
            time (datetime, optional): The time to convert to ISO 8601 format (default is None, which uses the current NTP time).

        Returns:
            str: The time in ISO 8601 format.

        ISO 8601 format: "YYYY-MM-DDTHH:MM:SSZ"
        """
        if time is None:
            time = self.get_ntp_time()
        return time.strftime("%Y-%m-%dT%H:%M:%SZ")