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

import sys
from Logger.logger import logger
from server.rest import APIServer

class Outliers:
    def __init__(self) -> None:
        logger.info("Starting Outliers API REST")
        self.api = APIServer()
        logger.info("Starting Outliers Server")
        if len(sys.argv) > 1:
            self.api.start_server(True)
        else:
            self.api.start_server(False)

Outliers_ = Outliers()