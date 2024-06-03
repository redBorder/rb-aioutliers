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

import psycopg2
from resources.src.server.rest import config
from resources.src.logger.logger import logger

class RbOutliersPSQL:

    RB_AIOUTLIERS_FILTERS_QUERY = "SELECT filter FROM saved_filters"

    @staticmethod
    def get_filtered_data(self):
        """
        Retrieves filters from the database.

        Establishes a connection to the PostgreSQL database using credentials from the config file,
        executes a query to fetch filters from the saved_filters table, and returns the list of filters.

        Args:
            self: Reference to the current instance of the class.

        Returns:
            List of filters fetched from the database.

        Raises:
            Logs any exception that occurs during database operations.

        Ensures:
            The database connection is closed after the operation.
        """
        connection = None
        try:
            connection = psycopg2.connect(
                host=config.get("rbpsql", "host"),
                database=config.get("rbpsql", "database"),
                user=config.get("rbpsql", "user"),
                password=config.get("rbpsql", "password")
            )
            
            cursor = connection.cursor()
            cursor.execute(self.RB_AIOUTLIERS_FILTERS_QUERY)
            filtered_data = cursor.fetchall()
            filters = [record[0] for record in filtered_data]
            cursor.close()
            
            return filters
            
        except (Exception, psycopg2.DatabaseError) as error:
            logger.error(error)
        
        finally:
            if connection is not None:
                connection.close()
