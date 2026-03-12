import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from resources.src.logger import logger

class ForecastingModel:
    """
    A statistical forecasting model to calculate predictions from data obtained from Druid.
    """

    def __init__(self):
        """
        Initializes the forecasting model.
        """
        self.rf_regressor = RandomForestRegressor(n_estimators=100, random_state=42)

    def calculate_predictions(self, raw_json):
        """
        Retrieves data from Druid and calculates predictions using the last two weeks of data.

        Args:
            raw_json (Json): JSON response from Druid containing the data.

        Returns:
            (Json): JSON with the calculated forecasted values.
        """
        try:
            data = pd.DataFrame(raw_json)  # Convert JSON into DataFrame without considering column names

            if data.shape[1] < 2:
                raise ValueError("The JSON does not have the expected format. Two columns are required: timestamp and value.")

            # The first column is the timestamp, the second is the value
            data.columns = ["timestamp", "value"]

            # Convert timestamps to datetime
            data["timestamp"] = pd.to_datetime(data["timestamp"])
            data.set_index("timestamp", inplace=True)

            # Filter the last two weeks of data (if enough data is available)
            two_weeks_ago = data.index.max() - pd.Timedelta(days=14)
            data = data.loc[data.index >= two_weeks_ago]

            if len(data) < 2:
                logger.warning("Not enough data in the last two weeks, using available data instead.")

            # Prepare data for the model
            X_train = np.array([data["value"][:-1]]).reshape(-1, 1)
            y_train = data["value"][1:].values

            if len(X_train) < 2:
                raise ValueError("Not enough data to train the model.")

            # Train the model
            self.rf_regressor.fit(X_train, y_train)

            # Make predictions (one prediction per data point)
            y_pred = self.rf_regressor.predict(X_train)

            # Format predictions into JSON
            timestamps_pred = data.index[1:].to_numpy(dtype=str)
            predictions_series = pd.DataFrame({"timestamp": timestamps_pred, "forecasted": y_pred})

            return {"forecasted": predictions_series.to_dict(orient="records"), "status": "success"}

        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            return {"error": str(e)}
