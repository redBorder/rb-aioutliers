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

import os
import sys
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

from resources.src.logger import logger

class ShallowOutliers:
    """
    Shallow AI model for detecting outliers in 1-dimensional data. Utilized when a deep learning model is not defined.

    Args:
        sensitivity (float, optional): A value between 0 and 1 that adjusts the threshold for identifying anomalies.
            At 1, at least one anomaly is always identified. At 0, no anomalies are identified. Default is 0.95.
        
        contamination (float, optional): A value between 0 and 1 that indicates the proportion of data points
            to be considered anomalous during training. Default is 0.01.
    """

    def __init__(self, sensitivity=0.95, contamination=0.01):
        """
        Initializes the ShallowOutliers model.

        Args:
            sensitivity (float, optional): A value between 0 and 1 that adjusts the threshold for identifying anomalies.
                At 1, at least one anomaly is always identified. At 0, no anomalies are identified. Default is 0.95.

            contamination (float, optional): A value between 0 and 1 that indicates the proportion of data points
                to be considered anomalous during training. Default is 0.01.
        """
        self.sens = sensitivity
        self.cont = contamination


    def predict(self, arr):
        """
        Given an array of data points, makes a smoothed prediction of the data. To do so,
        a weighted average of each point with it surroundings is done where about half of
        the weight is assigned to the original point and the rest is distributed
        proportionally to the distance to it.

        Args:
            arr (numpy.ndarray): 1D numpy array with the datapoints to be smoothed.

        Returns:
            smooth_arr (numpy.ndarray): 1D numpy array with the smoothed data. Same shape as arr.
        """
        if len(arr) == 0:
            error_msg = "Input array must be non-empty"
            logger.logger.error(error_msg)
            raise ValueError(error_msg)
        if arr.ndim != 1:
            error_msg = "Input array must be 1-dimensional"
            logger.logger.error(error_msg)
            raise ValueError(error_msg)
        if not np.issubdtype(arr.dtype, np.number):
            error_msg = "Input array must contain numerical data"
            logger.logger.error(error_msg)
            raise ValueError(error_msg)

        window_size = max(int(0.05 * len(arr)), min(len(arr), int(5 + np.log(len(arr)))))
        window_size += 1 if window_size % 2 == 0 else 0
        half_size = window_size // 2
        kernel = np.linspace(1, half_size, half_size, dtype=float)
        kernel = np.concatenate((kernel, [half_size**2 * 0.25], kernel[::-1]))
        kernel /= kernel.sum()
        padded_arr = np.pad(arr, half_size, mode='edge')
        smooth_arr = np.convolve(padded_arr, kernel, mode='valid')
        return smooth_arr

    def get_outliers(self, arr, smoothed_arr, other=None):
        """
        Given an array of data points and an aproximation of it, return a boolean array
        with the same shape as the original array which is True when the data point is
        an outlier and False otherwise.

        The method used for outlier detection is an isolation forest, which will look for
        the 1% most isolated points when taking into account the original value, the
        smoothed valued, the absolute diference between them (MAE) and the sign of the
        difference between them.

        Args:
            arr (numpy.ndarray): 1D numpy array where the outliers shall be detected.
            smoothed_arr (numpy.ndarray): 1D numpy array that tries to approximate arr.
                -Must have the same shape as arr.

        Returns:
            numpy.ndarray: 1D numpy array with the smoothed data.
        """
        error = arr-smoothed_arr
        sign = np.sign(error)
        data = np.stack((smoothed_arr, np.abs(error), sign), axis=1)
        if other is not None:
            data = np.concatenate([data, other], axis=1)
        model = IsolationForest(n_estimators=100, contamination=self.cont, random_state=42)
        model.fit(data)
        model.offset_=self.sens*(1+model.offset_)-1
        outliers = model.predict(data)==-1
        return outliers

    def encode_timestamp(self, timestamp):
        """
        Takes a pandas Series of timestamps and returns a numpy array with a sine encoding for the
        hour of day and a cosine encoding for the day of the week. This encoding helps the model to
        learn periodic patterns in the data while maintaining simplicity.
        
        Args:
            timestamps (pd.Series): A Pandas Series of timestamps.
        
        Returns:
            pd.DataFrame: A DataFrame with sine-cosine encodings for daily and weekly periods.
        """
        if not isinstance(timestamp, pd.Series):
            raise ValueError("Input must be a Pandas Series")
        timestamp = pd.to_datetime(timestamp)
        hour_of_day = timestamp.dt.hour + timestamp.dt.minute/60
        day_of_week = timestamp.dt.dayofweek + hour_of_day/24
        daily_sin = np.sin(2*np.pi*hour_of_day/24)
        weekly_cos = np.cos(2*np.pi*day_of_week/7)
        encoded = np.stack((daily_sin, weekly_cos), axis=1)
        return encoded

    def compute_json(self, raw_json):
        """
        Main method used for anomaly detection.

        Make the model process Json data and output to RedBorder prediction Json format.
        It includes the prediction for each timestamp and the anomalies detected.

        Args:
            raw_json (Json): druid Json response with the data.

        Returns:
            (Json): Json with the anomalies and predictions for the data with RedBorder prediction
              Json format.
        """
        data = pd.json_normalize(raw_json)
        arr = data.iloc[:, 1].values
        smoothed_arr = self.predict(arr)
        encoded_timestamp = self.encode_timestamp(data["timestamp"])
        outliers = self.get_outliers(arr, smoothed_arr, other=encoded_timestamp)
        data["smooth"] = smoothed_arr
        predicted = data[["timestamp","smooth"]].rename(columns={"smooth":"forecast"})
        anomalies = data[["timestamp","smooth"]].rename(columns={"smooth":"expected"}).loc[outliers]
        return  {
            "anomalies":anomalies.to_dict(orient="records"),
            "predicted":predicted.to_dict(orient="records"),
            "status": "success"
        }

    def execute_prediction_model(self, data):
        try:
            return self.compute_json(data)
        except Exception as e:
            logger.logger.error("Could not execute shallow model")
            return self.return_error(e)

    @staticmethod
    def return_error(error="error"):
        """
        Returns an adequate formatted JSON for whenever there is an error.

        Args:
            error (string): message detailing what type of error has been fired.
        """
        return { "status": "error", "msg":error }
