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
from gunicorn.app.base import BaseApplication

class GunicornApp(BaseApplication):
    def __init__(self, app, options=None):
        """
        Initialize a Gunicorn application.

        Args:
            app: The WSGI application to run.
            options (dict, optional): Additional Gunicorn options (default is None).
        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """
        Load Gunicorn configuration settings based on provided options.
        """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key, value)

    def load(self):
        """
        Load the WSGI application to be run by Gunicorn.

        Returns:
            object: The WSGI application to run.
        """
        return self.application.app