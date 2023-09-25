# Copyright (C) 2023 Eneo Tecnologia S.L.
#
# Authors :
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

import os
'''
Start of important OS Variables
'''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '1'
'''
End of important OS Variables
'''
import pytz
import json
import time
import random
import datetime
import numpy as np
import configparser
import pandas as pd
import tensorflow as tf
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler

class Autoencoder:
    """
    Autoencoder class for anomaly detection.

    Args:
        model_file (str): Path to model .keras file.
        model_config (dict): Model parameters (metrics, timestamps, granularities, etc...)
    """
    def __init__(self, model_file, model_config_file):
        """
        Initializes the Autoencoder model and defines constants.

        Args:
            model_file (str): Path to model .keras file.
            model_config_file (str): Path to the model config, including:
                METRICS (list): Names of the metrics used by the module.
                TIMESTAMP (list): Names of the timestamp columns used by the module.
                GRANULARITIES (list): Possible granularities.
                AVG_LOSS (float): Average loss of the model.
                STD_LOSS (float): Standard deviation of the loss of the model.
                WINDOW_SIZE (int): Number of entries the model will put together in a 'window'.
                NUM_WINDOWS (int): Number of windows the model will put together in each slice.
                LOSS_MULT_1 (float): Extra penalty in the loss function for guessing wrong metrics.
                LOSS_MULT_2 (float): Extra penalty in the loss function for guessing wrong 'minute' field.
        """

        try:
            model_config = configparser.ConfigParser()
            model_config.read(model_config_file)
            columns_section = model_config['Columns']
            self.METRICS = columns_section.get('METRICS', '').split(', ')
            self.TIMESTAMP = columns_section.get('TIMESTAMP', '').split(', ')
            self.GRANULARITIES = columns_section.get('GRANULARITIES', '').split(', ')
            self.COLUMNS = self.METRICS + self.TIMESTAMP + self.GRANULARITIES
            general_section = model_config['General']
            self.AVG_LOSS = float(general_section.get('AVG_LOSS', 0.0))
            self.STD_LOSS = float(general_section.get('STD_LOSS', 0.0))
            self.WINDOW_SIZE = int(general_section.get('WINDOW_SIZE', 0))
            self.NUM_WINDOWS = int(general_section.get('NUM_WINDOWS', 0))
            self.LOSS_MULT_1 = float(general_section.get('LOSS_MULT_1', 0))
            self.LOSS_MULT_2 = float(general_section.get('LOSS_MULT_2', 0))
        except FileNotFoundError:
            print(f"Error: Model file '{model_config_file}' not found.")
        except (OSError, ValueError) as e:
            print(f"Error loading model conif: {e}")

        try:
            self.model = tf.keras.models.load_model(
                model_file,
                compile=False
                #custom_objects={'weighted_loss': self.model_loss}
            )
            self.model.loss = self.model_loss
            self.model.compile()
        except FileNotFoundError:
            print(f"Error: Model file '{model_file}' not found.")
        except (OSError, ValueError) as e:
            print(f"Error loading the model: {e}")

    def rescale(self, data):
        """
        Rescale data between 0-1.
        For a metric x, the rescaling function is tanh(ln(x+1)/32).
        For the minute field, it is rescaled by dividing the number between 1440.

        Args:
            data (numpy.ndarray): Input data as a numpy array.

        Returns:
            numpy.ndarray: Rescaled data as a numpy array.
        """
        num_metrics = len(self.METRICS)
        rescaled=data.copy()
        rescaled[..., 0:num_metrics]=np.tanh(np.log1p(rescaled[..., 0:num_metrics])/32)
        rescaled[..., num_metrics]=rescaled[..., num_metrics]/1440
        return rescaled

    def descale(self, data):
        """
        Descale data to original scale.

        Args:
            data (numpy.ndarray): Input data as a numpy array.

        Returns:
            numpy.ndarray: Descaled data as a numpy array.
        """
        num_metrics = len(self.METRICS)
        descaled = data.copy()
        descaled = np.where(descaled > 1.0, 1.0, np.where(descaled < -1.0, -1.0, descaled))
        descaled[..., 0:num_metrics] = np.expm1(32*np.arctanh(descaled[..., 0:num_metrics]))
        descaled[..., num_metrics]=descaled[..., num_metrics]*1440
        return descaled

    def model_loss(self, y_true, y_pred, single_value=True):
        """
        Calculate the weighted loss for the model.
        Compares the input with boolean-valued tensors IS_METRIC and IS_MINUTE.
        Where IS_METRIC is true, the value of the input is multiplied by mult1,
        where IS_MINUTE is true, the value of the input is multiplied by mult2,
        otherwise, the value is left unchanged.
        Then, the difference between both tensors is evaluated and a log_cosh loss
        is applied.
        
        Args:
            y_true (tf.Tensor): True target values.
            y_pred (tf.Tensor): Predicted values.
            single_value (bool): Set to False to return a 3D array with the loss on each timestamp.

        Returns:
            tf.Tensor: Weighted loss value or a 3D loss array.
        """
        y_true = tf.cast(y_true, tf.float16)
        y_pred = tf.cast(y_pred, tf.float16)
        num_metrics = len(self.METRICS)
        num_features = len(self.COLUMNS)
        IS_METRIC = (tf.range(num_features) < num_metrics)
        IS_MINUTE = (tf.range(num_features) == num_metrics)
        mult_true = tf.where(IS_METRIC, self.LOSS_MULT_1 * y_true, tf.where(IS_MINUTE, self.LOSS_MULT_2 * y_true, y_true))
        mult_pred = tf.where(IS_METRIC, self.LOSS_MULT_1 * y_pred, tf.where(IS_MINUTE, self.LOSS_MULT_2 * y_pred, y_pred))
        standard_loss = tf.math.log(tf.cosh((mult_true - mult_pred)))

        if single_value:
            standard_loss = tf.reduce_mean(standard_loss)
        return standard_loss

    def slice(self, data, index = []):
        #TODO add a graph to doc to explain this
        """
        Transform a 2D numpy array into a 3D array readable by the model.

        Args:
            data (numpy.ndarray): 2D numpy array with the data to prepare.
            index (list): Index in case you want only some of the slices returned.

        Returns:
            numpy.ndarray: 3D numpy array that can be processed by the model.
        """
        _l = len(data)
        Xs = []
        slice_length = self.WINDOW_SIZE * self.NUM_WINDOWS
        if len(index) == 0:
            index = np.arange(0, _l-slice_length+1 , self.WINDOW_SIZE)
        for i in index:
            Xs.append(data[i:i+slice_length])
        return np.array(Xs)

    def flatten(self, data):
        """
        Flatten a 3D numpy array used by the model into a human-readable 2D numpy array.
        Args:
            data (numpy.ndarray): 3D numpy array.
        Returns:
            numpy.ndarray: 2D numpy array with the natural format of the data.
        """
        tsr = data.copy()
        num_slices, slice_len, features = tsr.shape
        flattened_len = (num_slices-1)*self.WINDOW_SIZE + slice_len
        flattened_tensor = np.zeros([flattened_len, features])
        scaling = np.zeros(flattened_len)
        for i in range(num_slices):
            left_pad = i*self.WINDOW_SIZE
            right_pad = left_pad+slice_len
            flattened_tensor[left_pad:right_pad] += tsr[i]
            scaling[left_pad:right_pad] +=1
        flattened_tensor = flattened_tensor / scaling[:, np.newaxis]
        return flattened_tensor

    def calculate_predictions(self, data):
        """
        Proccesses the data, calculates the prediction and its loss.

        Args:
            data (numpy.ndarray): 2D numpy array with the relevant data.
        Returns:
            predicted (numpy.ndarray): predicted data
            anomalies (numpy.ndarray): anomalies detected
            loss (numpy.ndarray): loss function for each entry
        """
        prep_data = self.slice(self.rescale(data))
        predicted = self.model.predict(prep_data)
        loss = self.flatten(self.model_loss(prep_data, predicted, single_value = False).numpy())
        predicted = self.descale(self.flatten(predicted))
        return predicted, loss

    def compute_json(self, metric, raw_json):
        """
        Main method used for anomaly detection.

        Make the model process Json data and output to RedBorder prediction Json format.
        It includes the prediction for each timestamp and the anomalies detected.

        Args:
            metric (string): the name of field being analyzed.
            raw_json (Json): druid Json response with the data.

        Returns:
            (Json): Json with the anomalies and predictions for the data with RedBorder prediction Json format.
        """
        threshold = self.AVG_LOSS+5*self.STD_LOSS
        data, timestamps = self.input_json(raw_json)
        predicted, loss = self.calculate_predictions(data)
        predicted = pd.DataFrame(predicted, columns=self.COLUMNS)
        predicted['timestamp'] = timestamps
        anomalies = predicted[loss>threshold]
        return self.output_json(metric, anomalies, predicted)

    def granularity_from_dataframe(self, dataframe):
        """
        Extract the granularity from a dataframe

        Args:
            dataframe (pd.DataFrame): Dataframe with timestamp column
        
        Returns:
            (int): Estimated Granularity of the dataframe.
        """
        stripped_granularities = [int(interval.split('_')[1].rstrip('m')) for interval in self.GRANULARITIES]
        time_diffs = pd.to_datetime(dataframe["timestamp"]).diff().dt.total_seconds() / 60
        average_gap = time_diffs.mean()
        return min(stripped_granularities, key=lambda x: abs(x - average_gap))

    def input_json(self, raw_json):
        """
        Transform Json data into numpy.ndarray readable by the model.
        Also returns the timestamps for each entry.

        Args:
            raw_json (Json): druid Json response with the data.
        
        Returns:
            data (numpy.ndarray): transformed data.
            timestamps (pd.Series): pandas series with the timestamp of each entry. 
        """
        data = pd.json_normalize(raw_json)
        gran_num = self.granularity_from_dataframe(data)
        gran = f"gran_{gran_num}m"
        data[self.GRANULARITIES] = (pd.Series(self.GRANULARITIES) == gran).astype(int)
        metrics_dict = {f"result.{metric}": metric for metric in self.METRICS}
        data.rename(columns=metrics_dict, inplace=True)
        timestamps = data['timestamp'].copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data['minute'] = data['timestamp'].dt.minute + 60 * data['timestamp'].dt.hour
        data = pd.get_dummies(data, columns=['timestamp'], prefix=['weekday'], prefix_sep='_', drop_first=True)
        missing_columns = set(self.COLUMNS) - set(data.columns)
        data[list(missing_columns)] = 0
        data = data[self.COLUMNS].dropna()
        data_array = data.values
        return data_array, timestamps

    def output_json(self, metric, anomalies, predicted):
        #TODO think if return should be Json or Json array
        """
        Transform Json data into numpy.ndarray readable by the model.
        Also returns the timestamps for each entry.

        Args:
            metric (string): the name of field being analyzed.
            anomalies (numpy.ndarray): anomalies detected by the model.
            predicted (numpy.ndarray): predictions made by the model.

        Returns:
            (Json): Json with the anomalies and predictions for the data with RedBorder prediction Json format.
        """
        predicted = predicted.copy()
        anomalies = anomalies.copy()
        predicted.rename(columns={metric:"forecast"},inplace=True)
        predicted = predicted[["forecast",'timestamp']].to_dict(orient="records")
        anomalies.rename(columns={metric:"expected"},inplace=True)
        anomalies = anomalies[["expected",'timestamp']].to_dict(orient="records")
        return  {
            "anomalies":anomalies,
            "predicted":predicted,
            "status": "success"
        }

    @staticmethod
    def execute_prediction_model(data, metric, model_file, model_config):
        autoencoder = Autoencoder(model_file, model_config)
        result = autoencoder.compute_json(metric, data)
        return result
    @staticmethod
    def return_error(error="error"):
        return { "status": "error", "msg":error }