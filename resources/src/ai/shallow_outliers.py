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

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

class ShallowOutliers:
    """
    Shallow AI model for outliers detection. Used whenever there is no deep learning model defined.
    Input data should be 1-dimensional.

    Args:
        (None)
    """
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
            raise ValueError("Input array must be non empty")
        if arr.ndim != 1:
            raise ValueError("Input array must be 1-dimensional")
        if not np.issubdtype(arr.dtype, np.number):
            raise ValueError("Input array must contain numerical data")
        window_size = max(int(0.05 * len(arr)), min(len(arr), int(5 + np.log(len(arr)))))
        window_size += 1 if window_size % 2 == 0 else 0
        kernel = np.arange(1, window_size // 2 + 2, dtype=float)
        kernel = np.concatenate((kernel, kernel[-2::-1]))
        kernel[window_size // 2] = 0.25*window_size ** 2
        kernel /= np.sum(kernel)
        padded_arr = np.pad(arr, (window_size // 2, window_size // 2), mode='edge')
        smooth_arr = np.convolve(padded_arr, kernel, mode='valid')
        return smooth_arr


    def get_outliers(self, arr, smoothed_arr):
        """
        Given an array of data points and an aproximation of it, return a boolean array
        with the same shape as the original array which is True when the data point is
        an outlier and False otherwise.

        The method used for outlier detection is an isolation forest, which will look for
        the 0.3% most isolated points when taking into account the original value, the 
        smoothed valued, the diference between them (error) and the squared diference
        between them.

        Args:
            arr (numpy.ndarray): 1D numpy array where the outliers shall be detected.
            smoothed_arr (numpy.ndarray): 1D numpy array that tries to approximate arr.
                -Must have the same shape as arr.
        
        Returns:
            numpy.ndarray: 1D numpy array with the smoothed data.
        """
        error = arr-smoothed_arr
        loss = error**2
        data = np.stack((arr,smoothed_arr,error,loss), axis = 1)
        model = IsolationForest(n_estimators=100, contamination=0.003)
        model.fit(data)
        outliers = model.predict(data)==-1
        return outliers

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
        outliers = self.get_outliers(arr, smoothed_arr)
        data["smooth"] = smoothed_arr
        predicted = data[["timestamp","smooth"]].rename(columns={"smooth":"forecast"})
        anomalies = data[["timestamp","smooth"]].rename(columns={"smooth":"expected"}).loc[outliers]
        return  {
            "anomalies":anomalies.to_dict(orient="records"),
            "predicted":predicted.to_dict(orient="records"),
            "status": "success"
        }

    @staticmethod
    def execute_prediction_model(data):
        shallow_outliers = ShallowOutliers()
        result = shallow_outliers.compute_json(data)
        return result

    @staticmethod
    def return_error(error="error"):
        return { "status": "error", "msg":error }
