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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.druid import query_builder

class TestQueryBuilder(unittest.TestCase):
    def setUp(self) -> None:
        aggregations_file = os.path.join(os.getcwd(),"resources", "src", "druid", "data", "aggregations.json")
        post_aggregations_file = os.path.join(os.getcwd(),"resources",  "src", "druid", "data", "postAggregations.json")
        self.builder = query_builder.QueryBuilder(aggregations_file, post_aggregations_file)

    def test_known_granularities_granularities_to_seconds(self):
        test_cases = [
            ("minute", 60),
            ("pt2h", 7200),
            ("P1D", 86400),
            # Add more known granularities and expected results here
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
            self.builder.granularity_to_seconds(None)  # Test with None input
        with self.assertRaises(ValueError):
            self.builder.granularity_to_seconds("")

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

    def test_modify_flow_sensor(self):
        query = {"filter": {"type": "selector", "dimension": "sensor_name", "value": "FlowSensor1"}}
        sensor = "FlowSensor2"
        modified_query = self.builder.modify_flow_sensor(query, sensor)
        self.assertEqual(modified_query["filter"]["value"], "FlowSensor2")

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