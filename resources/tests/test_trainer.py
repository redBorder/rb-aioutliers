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
import os
import sys
import logging
import json
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ai.trainer import Trainer

class TestTrainer(unittest.TestCase):

    def setUp(self):
        self.test_backup_path = "./test_backups/"
        os.makedirs(self.test_backup_path, exist_ok=True)
        self.trainer = Trainer("test_traffic.keras", "test_traffic.ini")
        self.trainer.model_config_file = "dummy_config.ini"
        self.trainer.model_file = "dummy.keras"

    def tearDown(self):
        os.rmdir(self.test_backup_path)
        os.remove("dummy_config.ini")
        os.remove("dummy.keras")

    def test_save_model(self):
        save_model_file = os.path.join(self.test_backup_path, "test_model.keras")
        save_config_file = os.path.join(self.test_backup_path, "test_config.ini")
        self.trainer.model = "dummy_model"
        self.trainer.METRICS = ["metric1", "metric2"]
        self.trainer.AVG_LOSS = 0.5
        self.trainer.STD_LOSS = 0.2
        self.trainer.save_model(save_model_file, save_config_file)
        self.assertTrue(os.path.exists(save_model_file))
        self.assertTrue(os.path.exists(save_config_file))

    def test_prepare_data_for_training(self):
        data = np.array([1, 2, 3, 4, 5])
        prep_data = self.trainer.prepare_data_for_training(data)

    def test_train(self):
        with open("outliers_test_data.json", "r") as file:
            raw_data = json.load(file)
        self.trainer.train(raw_data, epochs=10, batch_size=32, backup_path=self.test_backup_path)

if __name__ == "__main__":
    unittest.main()