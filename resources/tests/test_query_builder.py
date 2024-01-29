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


import unittest
import sys
import os
import json
import tempfile
from resources.src.druid import query_builder

class TestQueryBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.aggregations_file = os.path.join(os.getcwd(),"resources", "src", "druid", "data", "aggregations.json")
        self.post_aggregations_file = os.path.join(os.getcwd(),"resources",  "src", "druid", "data", "postAggregations.json")
        self.builder = query_builder.QueryBuilder(self.aggregations_file, self.post_aggregations_file)

    def test_nonexistent_files(self):
        with self.assertRaises(FileNotFoundError):
            query_builder.QueryBuilder("nonexist.json", self.post_aggregations_file)
        with self.assertRaises(FileNotFoundError):
            query_builder.QueryBuilder(self.aggregations_file, "nonexist.json")

    def test_nonjson_files(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        with self.assertRaises(ValueError):
            query_builder.QueryBuilder(temp_file_path, self.post_aggregations_file)
        with self.assertRaises(ValueError):
            query_builder.QueryBuilder(self.aggregations_file, temp_file_path)

    def test_known_granularities_granularities_to_seconds(self):
        test_cases = [
            ("minute", 60),
            ("pt2h", 7200),
            ("P1D", 86400),
        ]
        for granularity, expected_seconds in test_cases:
            with self.subTest(granularity=granularity):
                self.assertEqual(self.builder.granularity_to_seconds(granularity), expected_seconds)

    def test_case_insensitivity_granularities_to_seconds(self):
        self.assertEqual(self.builder.granularity_to_seconds("minute"), 60)
        self.assertEqual(self.builder.granularity_to_seconds("MINUTE"), 60)
        self.assertEqual(self.builder.granularity_to_seconds("MiNuTe"), 60)

    def test_numeric_granularities_to_seconds(self):
        self.assertEqual(self.builder.granularity_to_seconds("pt5m"), 300)
        self.assertEqual(self.builder.granularity_to_seconds("pt30m"), 1800)

    def test_invalid_input_granularities_to_seconds(self):
        with self.assertRaises(ValueError):
            self.builder.granularity_to_seconds(None)
        with self.assertRaises(ValueError):
            self.builder.granularity_to_seconds("")
        with self.assertRaises(ValueError):
            self.builder.granularity_to_seconds("pttenm")
        with self.assertRaises(ValueError):
            self.builder.granularity_to_seconds("x")

    def test_modify_granularity(self):
        query1 = {
            "granularity": {
                "period": "pt5m"
            }
        }
        query2 = {
            "granularity": {
                "period": "pt10m"
            }
        }
        self.assertEqual(self.builder.modify_granularity(query1, "pt10m"), query2)

    def test_modify_aggregations(self):
        query = {
            "granularity": {
                "period": "pt5m"
            }
        }
        modified_query = self.builder.modify_aggregations(query)
        self.assertTrue("aggregations" in modified_query)
        self.assertTrue("postAggregations" in modified_query)
        self.assertEqual(modified_query["granularity"]["period"], "pt5m")
        self.assertEqual(modified_query["postAggregations"][0]["fields"][1]["value"] , 300)

    def test_modify_filter(self):
        query = {"filter": {"type": "selector", "dimension": "sensor_name", "value": "FlowSensor"}}
        filter = {"type": "test1", "dimension": "test2", "value": "test3"}
        modified_query = self.builder.modify_filter(query, filter)
        self.assertEqual(modified_query["filter"], filter)

    def test_set_time_origin(self):
        query = {"granularity": {"origin": "2023-01-01T00:00:00Z"}}
        time = "2023-01-01T12:00:00Z"
        modified_query = self.builder.set_time_origin(query, time)
        self.assertEqual(modified_query["granularity"]["origin"], "2023-01-01T12:00:00Z")

    def test_set_time_interval(self):
        query = {}
        time_start = "2023-01-01T00:00:00Z"
        time_end = "2023-01-02T00:00:00Z"
        modified_query = self.builder.set_time_interval(query, time_start, time_end)
        self.assertEqual(modified_query["intervals"], ["2023-01-01T00:00:00Z/2023-01-02T00:00:00Z"])

if __name__ == '__main__':
    unittest.main()