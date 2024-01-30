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
import logging
from pylogrus import PyLogrus

from resources.src.config import configmanager

class CustomFormatter(logging.Formatter):
    def __init__(self, fmt=None, datefmt=None):
        """
        Initialize a custom log formatter.

        Args:
            fmt (str, optional): The log format string (default is None).
            datefmt (str, optional): The date/time format string (default is None).
        """
        super().__init__(fmt, datefmt)

    def format(self, record):
        """
        Format a log record into a custom log message.

        Args:
            record (LogRecord): The log record to be formatted.

        Returns:
            str: The formatted log message.

        This method is called for each log record to create a custom log message.
        """
        log_time = self.formatTime(record)
        log_level = record.levelname
        log_message = record.getMessage()
        return f"[[{log_time}]]\t{log_level} {log_message}"

class Logger:
    def __init__(self, log_level=logging.INFO, log_file=None):
        """
        Initialize a custom logger.

        Args:
            log_level (int, optional): The log level (default is logging.INFO).
            log_file (str, optional): The path to the log file (default is './outliers.log').

        If log_file is not provided, the default log file is './outliers.log', but it can be configured using ConfigManager.
        """
        if log_file is None:
            log_file = './outliers.log'
            try:
                from config import configmanager
                config = configmanager.ConfigManager(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "config.ini"))
                log_file = config.get('Logger', 'log_file')
            except Exception as e:
                print("Could not resolve ConfigManager, default set to ./outliers.log")
        self.logger = PyLogrus(name="Outlierslogger")
        log_dir = os.path.dirname(log_file)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if not os.path.isfile(log_file):
            with open(log_file, 'w') as f:
                pass
        console_handler = logging.StreamHandler()
        console_formatter = CustomFormatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
        console_handler.setFormatter(console_formatter)

        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_formatter = CustomFormatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
            file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        if log_file:
            self.logger.addHandler(file_handler)

        self.logger.setLevel(log_level)

    def get_log_file(self, config_file):
        """
        Get the path to the log file.

        Args:
            config_file (str): The path to the config file being used.

        Returns:
            (str): path to the log file.
        """

        try:
            return configmanager.ConfigManager(config_file).get('Logger', 'log_file')
        except Exception as e:
            print("Could not resolve ConfigManager, default set to ./outliers.log")
            return './outliers.log'


    def info(self, message):
        """
        Log an informational message.

        Args:
            message (str): The message to log.
        """
        self.logger.info(message)

    def debug(self, message):
        """
        Log a debug message.

        Args:
            message (str): The debug message to log.
        """
        self.logger.debug(message)

    def error(self, message):
        """
        Log an error message.

        Args:
            message (str): The error message to log.
        """
        self.logger.error(message)

logger = Logger()
