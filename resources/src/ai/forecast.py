import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from resources.src.logger import logger
from prophet import Prophet
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
            print("TIMEZONE----------------------")
            time_zone=str(data["timestamp"].tz)
            gran=self.granularity_from_dataframe(data)
            gran= int(gran)
            print("-------------Granularity:")
            print(gran)
            print(type(gran))
            data=self.data_handle(data,"Prophet")
            #print(data)
            predictions_df=self.execute_model(data,"Prophet",gran)
            #self.output_json(predictions_df)
            print(predictions_df)
            print(self.output_json(predictions_df))
            #df=pd.concat([predictions_df,data["y"]],axis=1)

            #data.set_index("timestamp", inplace=True)

            # Filter the last two weeks of data (if enough data is available)
            #two_weeks_ago = data.index.max() - pd.Timedelta(days=14)
            #data = data.loc[data.index >= two_weeks_ago]
#
            #if len(data) < 2:
            #    logger.warning("Not enough data in the last two weeks, using available data instead.")

            #return {"forecasted": predictions_series.to_dict(orient="records"), "status": "success"}

        except Exception as e:
            logger.error(f"Error in prediction: {str(e)}")
            return {"error": str(e)}


    def granularity_from_dataframe(self, dataframe):
        """
        Extract the granularity from a dataframe. The granularity is suposed to be the difference
        between successive timestamps.

        Args:
            dataframe (pandas.DataFrame): Dataframe with timestamp column

        Returns:
            time_diffs: Number in minutes with the estimated Granularity of the dataframe.
        """
        time_diffs = pd.to_datetime(dataframe["timestamp"]).diff().dt.total_seconds() // 60
        time_diffs.iloc[0] = time_diffs.iloc[1]
        time_diffs = time_diffs.where(time_diffs >= 0, time_diffs.shift(-1))
        gran=time_diffs.mode().iloc[0]

        return gran
    
    def data_handle(self, df, model):
        if model=="Prophet":
            df["value"] = df["value"].str["bytes"]
            df.rename(columns={"timestamp":"ds", "value":"y"}, inplace=True)
            df['ds']=df['ds'].dt.tz_localize(None)
        return df
    
    def execute_model(self,df, model, gran):
        
        p= df.shape[0]//10

        if model == "Prophet":
            m = Prophet()
            m.fit(df)
            frequency="".join([str(gran),"min"])
            
            future = m.make_future_dataframe(periods=p, freq= frequency)
            forecast=m.predict(future)
            forecast_df= forecast[["ds","yhat"]].tail(p)
        return forecast_df

    def output_json(self,df):
        df.rename(columns ={"ds":"timestamp","yhat":"forecast" },inplace=True)
        df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
        #df.set_index('timestamp', inplace=True)  

        return  {
            "predicted":df.to_dict(orient="records"),
            "status": "success"
        }
        
