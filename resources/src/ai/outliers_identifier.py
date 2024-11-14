# Copyright (C) 2024 Eneo Tecnologia S.L.
#
# Authors:
# Miguel Álvarez Adsuara <malvarez@redborder.com>
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

import json
import pandas as pd
from resources.src.logger import logger
from sklearn.ensemble import IsolationForest

class OutlierIdentifier:
    def __init__(self):
        self.df = None
        self.model = None

    def prepare_data(self, all_ips_data):
        """
        Prepare the data by flattening the input data, extracting relevant features, 
        and computing rolling statistics.

        Args:
            all_ips_data (dict): Dictionary containing time-series data for each IP.
        """
        flattened_data = []
        for ip, ip_data in all_ips_data.items():
            for entry in ip_data:
                flattened_data.append({
                    "ip": ip,
                    "timestamp": entry.get("timestamp"),
                    "bytes": entry.get("result", {}).get("bytes", 0),
                })

        self.df = pd.DataFrame(flattened_data)
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df['hour'] = self.df['timestamp'].dt.hour
        self.df['minute'] = self.df['timestamp'].dt.minute
        self.df['day'] = self.df['timestamp'].dt.day
        self.df['dayofweek'] = self.df['timestamp'].dt.dayofweek
        self.df['dayofyear'] = self.df['timestamp'].dt.dayofyear

        self.df['rolling_mean'] = self.df['bytes'].rolling(window=5, min_periods=1).mean()
        self.df['rolling_std'] = self.df['bytes'].rolling(window=5, min_periods=1).std()

        self.df['rolling_mean'] = self.df['rolling_mean'].fillna(0)
        self.df['rolling_std'] = self.df['rolling_std'].fillna(0)

        self.df['low_traffic'] = self.df['bytes'] == 0

    def train_model(self, X_train):
        """
        Train the Isolation Forest model on the provided training data.

        Args:
            X_train (DataFrame): The training set features.
        """
        self.model = IsolationForest(contamination=0.05, random_state=42)
        self.model.fit(X_train)

    def identify_implicated_ips(self, outliers):
        """
        Identify IPs that contributed to the outlier events.

        Args:
            outliers (list): A list of outlier events with timestamps and expected values.
        
        Returns:
            dict: A dictionary with implicated IPs for each outlier event.
        """
        self.df['outlier'] = self.model.predict(self.df[['hour', 'minute', 'day', 'dayofweek', 'dayofyear', 'rolling_mean', 'rolling_std', 'low_traffic']])
        self.df['outlier'] = self.df['outlier'].apply(lambda x: 'anomaly' if x == -1 else 'normal')

        implicated_ips = {"ips": []}
        for outlier in outliers:
            timestamp = outlier["timestamp"]
            outlier_data = self.df[self.df['timestamp'] == timestamp]

            implicated_ips["ips"].append({
                "caused_by": list(outlier_data[outlier_data['outlier'] == 'anomaly']['ip'])
            })

        return implicated_ips

    def execute(self, outliers, all_ips_data):
        """
        Execute the full pipeline for detecting outliers and identifying implicated IPs.

        Args:
            outliers (list): A list of outlier events.
            all_ips_data (dict): Dictionary containing time-series data for each IP.

        Returns:
            json: A JSON string with the implicated IPs and outlier information.
        """
        self.prepare_data(all_ips_data)
        self.train_model(self.df[['hour', 'minute', 'day', 'dayofweek', 'dayofyear', 'rolling_mean', 'rolling_std', 'low_traffic']])

        implicated_ips = self.identify_implicated_ips(outliers)
        
        logger.logger.error(implicated_ips)
        
        return json.dumps(implicated_ips) if implicated_ips else {"ips": []}

    def train_and_execute_model(self, outliers, all_ips_data):
        """
        Wrapper function to handle errors during model training and execution.

        Args:
            outliers (list): A list of outliers to process.
            all_ips_data (dict): Dictionary of IP data.

        Returns:
            json: A JSON response with the result or error message.
        """
        try:
            return self.execute(outliers, all_ips_data)
        except Exception as e:
            logger.logger.error("Could not execute anomaly detection")
            return self.return_error(e)

    def return_error(self, error="error"):
        """
        Return a JSON formatted error message.

        Args:
            error (str): The error message to return.

        Returns:
            dict: A dictionary containing the error status and message.
        """
        return { "status": "error", "msg": error }