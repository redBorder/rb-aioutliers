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
import os
'''
Start of important OS Variables
'''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
'''
End of important OS Variables
'''
import sys
import json
import tempfile
import numpy as np
import tensorflow as tf

from resources.src.ai.outliers import Autoencoder

class TestAutoencoder(unittest.TestCase):
    main_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src")
    def setUp(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        data_file_path = os.path.join(current_dir, "outliers_test_data.json")
        with open(data_file_path, "r") as data_file:
            self.sample_data = json.load(data_file)
        self.autoencoder=Autoencoder(
            os.path.join(self.main_dir, "ai", "traffic.keras"),
            os.path.join(self.main_dir, "ai", "traffic.ini")
        )

    def test_model_execution_with_no_data(self):
        result = Autoencoder.execute_prediction_model(
            self.autoencoder,
            {},
            "bytes"
        )
        self.assertEqual(
            result['status'],
            'error'
        )
    def test_model_execution_with_no_metric(self):
        result = Autoencoder.execute_prediction_model(
            self.autoencoder,
            self.sample_data,
            ""
        )
        self.assertEqual(
            result['status'],
            'error'
        )
    def test_model_execution_with_too_little_data(self):
        result = Autoencoder.execute_prediction_model(
            self.autoencoder,
            self.sample_data[:10],
            "bytes"
        )
        self.assertEqual(
            result['status'],
            'error'
        )
    def test_model_execution_with_sample_data(self):
        Autoencoder.execute_prediction_model(
            self.autoencoder,
            self.sample_data,
            "bytes",
        )
    def test_invalid_model(self):
        with self.assertRaises(FileNotFoundError):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "test.keras"),
                os.path.join(self.main_dir, "ai", "traffic.ini")
            )

    def test_invalid_config(self):
        with self.assertRaises(FileNotFoundError):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "traffic.keras"),
                os.path.join(self.main_dir, "ai", "test.ini")
            )

    def test_load_empty_model(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        with self.assertRaises(Exception):
            Autoencoder(
                os.path.join(temp_file_path),
                os.path.join(self.main_dir, "ai", "traffic.ini")
            )
    def test_load_empty_conifg(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file_path = temp_file.name
        with self.assertRaises(Exception):
            Autoencoder(
                os.path.join(self.main_dir, "ai", "traffic.keras"),
                os.path.join(temp_file_path)
            )

    def test_flatten_slice_identity(self):
        np.random.seed(0)
        rand_data = np.random.rand(32, 3)
        sliced_data = self.autoencoder.slice(rand_data)
        flattened_data = self.autoencoder.flatten(sliced_data)
        self.assertTrue(np.allclose(flattened_data, rand_data))

    def test_scale_descale_identity(self):
        np.random.seed(0)
        rand_data = np.random.rand(32, len(self.autoencoder.columns))
        rescaled_data = self.autoencoder.rescale(rand_data.copy())
        descaled_data = self.autoencoder.descale(rescaled_data)
        self.assertTrue(np.allclose(descaled_data, rand_data))

    def test_loss_execution_single_value(self):
        np.random.seed(0)
        y_true = tf.random.uniform((32, len(self.autoencoder.columns)), dtype=tf.float16)
        y_pred = tf.random.uniform((32, len(self.autoencoder.columns)), dtype=tf.float16)
        try:
            loss = self.autoencoder.model_loss(y_true, y_pred, single_value=True)
            execution_success = True
        except Exception as e:
            execution_success = False
            print(e)
        self.assertTrue(execution_success, "model_loss execution failed with an exception.")

    def test_loss_execution_3d_array(self):
        np.random.seed(0)
        y_true = tf.random.uniform((32, len(self.autoencoder.columns)), dtype=tf.float16)
        y_pred = tf.random.uniform((32, len(self.autoencoder.columns)), dtype=tf.float16)
        try:
            loss = self.autoencoder.model_loss(y_true, y_pred, single_value=False)
            execution_success = True
        except Exception as e:
            execution_success = False
            print(e)
        self.assertTrue(execution_success, "model_loss execution failed with an exception.")

if __name__ == '__main__':
    unittest.main()
