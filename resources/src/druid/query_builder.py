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


"""
Module to modify the druid queries so they can be
processed by the model.
"""

import json

class QueryBuilder:
    """
    Class used to modify the manager usual query to exctract data about
    more fields from a module.
    """
    def __init__(self, aggregations, post_aggregations):
        """
        Initializer of the class
        
        Args:
            aggregations (string): path to json file with the 'aggregations'
              value of the druid query.
            post_aggregations (string): path to json file with the 'postAggregations'
              value of the druid query.
        """
        try:
            with open(aggregations, encoding="utf-8") as agr:
                self.aggregations = json.load(agr)
            with open(post_aggregations, encoding="utf-8") as pagr:
                self.post_aggregations = json.load(pagr)
        except FileNotFoundError as exc:
            raise FileNotFoundError("One or both files not found.") from exc
        except json.JSONDecodeError as exc:
            raise ValueError("JSON decoding failed. Check the JSON format.") from exc

    def granularity_to_seconds(self, granularity):
        """
        Get the number of seconds for each possible druid
        granularity. For example, "pt2m" would return 120
        and "thirty_minute" would return 1800.

        Args:
            -granularity (string): druid granularity.
        Returns:
            - (int): number of seconds in the granularity.
        """
        if not isinstance(granularity, str):
            raise ValueError("Granularity must be a string")
        if len(granularity)==0:
            raise ValueError("Granularity must be a non-empty string")
        base_granularities = {
            "minute": 60, "hour": 3600, "day": 86400,
            "fifteen_minute": 900, "thirty_minute": 1800,
            "m": 60, "h": 3600, "d": 86400
            }
        granularity = granularity.lower()
        if granularity in base_granularities:
            return base_granularities[granularity]
        try:
            multiplier = base_granularities[granularity[-1]]
        except Exception as exc:
            raise Exception('Invalid granularity') from exc
        numbers = int(''.join(filter(str.isdigit, granularity)))
        return numbers * multiplier

    def modify_aggregations(self, query):
        """
        Modify a druid query to add every field the traffic module uses.
        Those are: "bytes", "pkts", "clients", "flows", "bps", "pps", "fps",
        "bytes_per_client" , "bytes_per_sec_per_client", "flows_per_client" 
        and "flows_per_sec_per_client".
        
        Args:
            -query: dicitionary with the druid query.
        Returns:
            -new_query: the modified query.
        """
        new_query=query.copy()
        new_query["aggregations"] = self.aggregations
        granularity = query.get("granularity", {}).get("period", "minute")
        spg = self.granularity_to_seconds(granularity)
        post_aggregations = json.dumps(self.post_aggregations)
        post_aggregations = post_aggregations.replace('"seconds_per_granularity"', str(spg))
        new_query["postAggregations"] = json.loads(post_aggregations)
        return new_query

    def modify_filter(self, query, filter):
        """
         a druid query to add sensors of the traffic module.
        
        Args:
            -query: dicitionary with the druid query.
            -filter: array with the flow sensorts
        Returns:
            -query: the modified query.
        """
        new_query=query.copy()
        new_query["filter"] = filter
        return new_query

    def set_time_origin(self, query, time):
        """
        Modify a druid query to change time origin
        
        Args:
            -query: dictionary with the druid query.
        Returns:
            -query: the modified query.
        """
        new_query=query.copy()
        new_query["granularity"]["origin"] = time
        return new_query

    def set_time_interval(self, query, time_start, time_end):
        """
        Modify a druid query to change time interval
        
        Args:
            -query: dictionary with the druid query.
            -time_start: the start time of the data to retrieve.
            -time_end: the end data oof the data to retrieve.
        Returns:
            -query: the modified query.
        """
        new_query=query.copy()
        new_query["intervals"] = [
            f"{time_start}/{time_end}"
        ]
        return new_query

