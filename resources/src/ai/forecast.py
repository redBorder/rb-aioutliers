import numpy as np
import pandas as pd
import json
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from resources.src.logger import logger

class ForecastingModel:
    """"
    
    A Random Forest-based forecasting model for time-series data.
    
    """
    def __init__(self, window_size=5):
        """
        
        Initializes the model with a Random Forest Regressor and a Standard Scaler for the normalisation of the data.
        
        """
        self.rf_regressor = RandomForestRegressor(n_estimators=50, random_state=30, criterion = 'absolute_error', max_depth=10, min_samples_split=5, max_samples=0.6)
        self.scaler = StandardScaler()
        self.window_size = window_size

    def calculate_predictions(self, raw_json, forecast_horizon=60):
        """
        
        Retrieves the Data from Druid and calculates the predictions within the las two weeks.
        Args:
            raw_json (Json): JSON response from Druid containing the data.
            forecast_horizon (int): Number of periods to forecast into the future.
        Returns:
            dict: Dictionary of predictions with timestamps and values.
        
        """
        try:
            data = pd.read_json(json.dumps(raw_json), orient='records')

            if data.shape[1] < 2:
                raise ValueError("The JSON does not have the expected format. Two columns are required: timestamp and value.")

            data.columns = ["timestamp", "value"]
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data["value"] = data["value"].apply(lambda x: x["bytes"])
            data.set_index("timestamp", inplace=True)

            two_weeks_ago = data.index.max() - pd.Timedelta(days=14)
            data = data.loc[data.index >= two_weeks_ago]

            if len(data) < self.window_size + 1:
                raise ValueError("Not enough data to train the model.")

            values = data["value"].values
            X_train = []
            y_train = []
            for i in range(len(values) - self.window_size):
                X_train.append(values[i:i + self.window_size])
                y_train.append(values[i + self.window_size])

            X_train = np.array(X_train)
            y_train = np.array(y_train)

            X_train_scaled = self.scaler.fit_transform(X_train)

            self.rf_regressor.fit(X_train_scaled, y_train)

            y_pred = self.rf_regressor.predict(X_train_scaled)
            actual_timestamps = data.index[self.window_size:]
            actual_prediction = pd.DataFrame({
                "timestamp": actual_timestamps,
                "value": y_pred
            }).set_index("timestamp")

            last_window = values[-self.window_size:].tolist()
            future_values = []

            for _ in range(forecast_horizon):
                input_scaled = self.scaler.transform([last_window])
                pred = self.rf_regressor.predict(input_scaled)[0]
                future_values.append(pred)

                last_window = last_window[1:] + [pred]


            future_timestamps = pd.date_range(data.index[-1], periods=forecast_horizon + 1, freq='T')[1:]
            future_prediction = pd.DataFrame({
                "timestamp": future_timestamps,
                "value": future_values
            }).set_index("timestamp")


            prediction = pd.concat([actual_prediction, future_prediction])

            pred_list = [
                {
                    "timestamp": str(index),
                    "result": {"bytes": row["value"]}
                }
                for index, row in prediction.iterrows()
            ]

            return pred_list

        except Exception as e:
            return {"error": str(e)}

    def calculate_metrics(self, raw_json):
        """
        Calculates evaluation metrics using time-series cross-validation.

        Args:
            raw_json (Json): JSON response from Druid containing the data.

        Returns:
            dict: Dictionary of averaged evaluation metrics across cross-validation folds.
        """
        try:
            data = pd.read_json(json.dumps(raw_json), orient='records')

            if data.shape[1] < 2:
                raise ValueError("The JSON does not have the expected format. Two columns are required: timestamp and value.")

            data.columns = ["timestamp", "value"]
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data["value"] = data["value"].apply(lambda x: x["bytes"])
            data.set_index("timestamp", inplace=True)

            two_weeks_ago = data.index.max() - pd.Timedelta(days=14)
            data = data.loc[data.index >= two_weeks_ago]

            if len(data) < self.window_size + 2:
                raise ValueError("Not enough data to compute metrics with the current window size.")

            # Create lag-based features
            values = data["value"].values
            X, y = [], []
            for i in range(len(values) - self.window_size):
                X.append(values[i:i + self.window_size])
                y.append(values[i + self.window_size])

            X = np.array(X)
            y = np.array(y)

            X_scaled = self.scaler.fit_transform(X)

            tscv = TimeSeriesSplit(n_splits=5)
            mae_list, r2_list, mape_list, smape_list = [], [], [], []

            for train_index, test_index in tscv.split(X_scaled):
                X_train_fold, X_test_fold = X_scaled[train_index], X_scaled[test_index]
                y_train_fold, y_test_fold = y[train_index], y[test_index]

                self.rf_regressor.fit(X_train_fold, y_train_fold)
                y_pred_fold = self.rf_regressor.predict(X_test_fold)

                mae_list.append(mean_absolute_error(y_test_fold, y_pred_fold))
                r2_list.append(r2_score(y_test_fold, y_pred_fold))
                mape_list.append(np.mean(np.abs((y_test_fold - y_pred_fold) / y_test_fold)) * 100)
                smape_list.append(
                    100 * np.mean(2 * np.abs(y_pred_fold - y_test_fold) / (np.abs(y_test_fold) + np.abs(y_pred_fold)))
                )

            return {
                'MAE': np.mean(mae_list) / 1e9,  # Assuming value is in bytes
                'R2': np.mean(r2_list),
                'MAPE': np.mean(mape_list),
                'SMAPE': np.mean(smape_list)
            }

        except Exception as e:
            return {"error": str(e)}
