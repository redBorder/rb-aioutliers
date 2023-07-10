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
import logging
from Config import configmanager
from pylogrus import PyLogrus, JsonFormatter

config = configmanager.ConfigManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"))

class CustomFormatter(logging.Formatter):
    def format(self, record):
        log_time = self.formatTime(record, self.datefmt)
        log_level = record.levelname
        log_message = record.getMessage()
        return f"[[{log_time}]]\t{log_level} {log_message}"

class Logger:
    def __init__(self, log_level=logging.INFO):
        log_file = config.get('Logger', 'log_file')
        self.logger = PyLogrus(name="OutliersLogger")

        console_handler = logging.StreamHandler()
        console_formatter = CustomFormatter("%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = CustomFormatter("%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        if log_file:
            self.logger.addHandler(file_handler)

        self.logger.setLevel(log_level)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def error(self, message):
        self.logger.error(message)

logger = Logger()