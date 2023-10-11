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
import json
import numpy as np
import configparser

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.ai.trainer import Trainer

class TestTrainer(unittest.TestCase):

    def setUp(self):
        self.test_backup_path = "./resources/tests/test_backups/"
        os.makedirs(self.test_backup_path, exist_ok=True)
        self.trainer = Trainer("./resources/tests/model_test.keras", "./resources/tests/model_test_config.ini")
        self.trainer.model_config_file = "./resources/tests/dummy_config.ini"
        self.trainer.model_file = "./resources/tests/dummy.keras"

    def tearDown(self):
        if os.path.exists(self.test_backup_path):
            for filename in os.listdir(self.test_backup_path):
                if os.path.isfile(os.path.join(self.test_backup_path, filename)):
                    os.remove(os.path.join(self.test_backup_path, filename))
            os.rmdir(self.test_backup_path)
        if os.path.isfile(os.path.join(self.trainer.model_config_file)):
            os.remove(self.trainer.model_config_file)
        if os.path.isfile(self.trainer.model_file):
            os.remove(self.trainer.model_file)

    def test_save_model(self):
        dummy_model = os.path.join(self.test_backup_path, "dummy.keras")
        dummy_config = os.path.join(self.test_backup_path, "dummy_config.ini")
        self.trainer.METRICS = ["metric1", "metric2"]
        self.trainer.AVG_LOSS = 0.5
        self.trainer.STD_LOSS = 0.2
        self.trainer.save_model(dummy_model, dummy_config)
        self.assertTrue(os.path.exists(dummy_model))
        self.assertTrue(os.path.exists(dummy_config))
        model_config = configparser.ConfigParser()
        model_config.read(dummy_config)
        columns_section = model_config['Columns']
        self.assertEqual(["metric1", "metric2"], columns_section.get('METRICS', '').split(', '))
        general_section = model_config['General']
        self.assertEqual('0.5', general_section.get('AVG_LOSS'))
        self.assertEqual('0.2', general_section.get('STD_LOSS'))

    def test_prepare_data_for_training(self):
        data = np.zeros((100,100))
        prep_data = self.trainer.prepare_data_for_training(data)
        self.assertEqual(prep_data.shape[1], self.trainer.NUM_WINDOWS*self.trainer.WINDOW_SIZE)
        self.assertEqual(prep_data.shape[2], 100)

    def test_train(self):
        with open("./resources/tests/outliers_test_data.json", "r") as file:
            raw_data = json.load(file)
        self.trainer.train(raw_data, epochs=10, batch_size=32, backup_path=self.test_backup_path)

if __name__ == "__main__":
    unittest.main()
