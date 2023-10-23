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


import configparser

class ConfigManager:
    def __init__(self, config_file):
        """
        Initialize a configuration manager.

        Args:
            config_file (str): The path to the configuration file to read and write.
        """
        self.config = configparser.ConfigParser()
        self.config.read(config_file)

    def get(self, section, option):
        """
        Get the value of an option in a section.

        Args:
            section (str): The section name.
            option (str): The option name.

        Returns:
            str: The value of the specified option in the specified section.
        """
        return self.config.get(section, option)

    def set(self, section, option, value):
        """
        Set the value of an option in a section.

        If the specified section does not exist, it will be created.

        Args:
            section (str): The section name.
            option (str): The option name.
            value (str): The value to set for the specified option.
        """
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, value)

    def save(self, config_file):
        """
        Save the configuration to a file.

        Args:
            config_file (str): The path to the file where the configuration should be saved.
        """
        with open(config_file, 'w') as f:
            self.config.write(f)
