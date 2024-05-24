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


import datetime
import unittest, sys, os

from resources.src.rbntp.ntplib import NTPClient

class TestNTPClient(unittest.TestCase):
    def test_get_ntp_time(self):
        ntp_client = NTPClient()
        ntp_time = ntp_client.get_ntp_time()
        self.assertTrue(isinstance(ntp_time, datetime.datetime))

    def test_get_substracted_day_time(self):
        ntp_client = NTPClient()
        ntp_time = ntp_client.get_ntp_time()
        subtracted_time = ntp_client.get_substracted_day_time(ntp_time)
        self.assertTrue(isinstance(subtracted_time, datetime.datetime))

    def test_time_to_iso8601_time(self):
        ntp_client = NTPClient()
        ntp_time = ntp_client.get_ntp_time()
        iso8601_time = ntp_client.time_to_iso8601_time(ntp_time)
        self.assertTrue(isinstance(iso8601_time, str))
        self.assertRegex(iso8601_time, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")

if __name__ == '__main__':
    unittest.main()