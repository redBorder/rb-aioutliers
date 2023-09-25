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

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.Druid import query_builder
class TestQueryBuilder(unittest.TestCase):
    def setUp(self) -> None:
        aggregations_file = os.path.join(os.getcwd(),"resources", "src", "Druid", "aggregations.json")
        post_aggregations_file = os.path.join(os.getcwd(),"resources",  "src", "Druid", "postAggregations.json")
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

if __name__ == '__main__':
    unittest.main()