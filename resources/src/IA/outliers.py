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
import pytz
import json
import random
import datetime
import numpy as np
import pandas as pd
import tensorflow as tf
from datetime import datetime
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, StandardScaler 

class KerasModel:
    def __init__(self, data_file, metric, model_file):
        self.data_file = data_file
        self.model_file = model_file
        self.metric = metric

    def standard_scale(self,dataframe):
        scaled = dataframe[self.standard_cols].copy()
        params = {}
        for col in self.standard_cols:
            if col != "clients":
                scaled[col]=np.log10(scaled[col])
            params[col]={ "mean":scaled[col].mean(), "std":scaled[col].std()}
        scaled=StandardScaler().fit_transform(scaled)
        return scaled, params

    def minmax_scale(self,dataframe):
        scaled = dataframe[self.minmax_cols].copy()
        params = {}
        for col in self.minmax_cols:
            params[col]={ "min":scaled[col].min(), "max":scaled[col].max()}
        scaled=MinMaxScaler().fit_transform(scaled)
        return scaled, params

    def rescale(self, dataframe):
        standard_data, standard_params = self.standard_scale(dataframe)
        minmax_data, minmax_params = self.minmax_scale(dataframe)
        rescaled_data=np.concatenate( [standard_data, minmax_data], axis=1 )
        self.standard_params = standard_params
        self.minmax_params = minmax_params
        return rescaled_data

    def standard_inverse_scale(self,dataframe):
        scaled=dataframe[self.standard_cols].copy()
        for col in self.standard_cols:
            scaled[col]=scaled[col]*self.standard_params[col]["std"]+self.standard_params[col]["mean"]
            if col!= "clients":
                scaled[col]= 10** scaled[col]
        return scaled

    def minmax_inverse_scale(self,dataframe):
        scaled=dataframe[self.minmax_cols].copy()
        for col in self.minmax_cols:
            scaled[col]=scaled[col]*(self.minmax_params[col]["max"]-self.minmax_params[col]["min"])+self.minmax_params[col]["min"] 
            if col!= "clients":
                scaled[col]= 10** scaled[col]
        return scaled
    
    def descale(self,dataframe):
        standard_data= self.standard_inverse_scale(dataframe)
        minmax_data = self.minmax_inverse_scale(dataframe)
        descaled_data=pd.concat( [standard_data, minmax_data], axis=1 )
        return descaled_data

    def extract_anomalies(self,data, predicted):
        loss = (data-predicted)**2
        loss = loss.mean(axis=(1,2))
        threshold = np.percentile(loss, self.percentile)
        anomalies = (loss > threshold)
        data_anomalies= pd.DataFrame(data[:,0]).loc[anomalies]
        predicted_anomalies = pd.DataFrame(predicted[:,0]).loc[anomalies]
        return data_anomalies, predicted_anomalies
    
    def output_formatting(self, anomalies, predicted, timestamp):
        predicted=pd.DataFrame(predicted[:,0])
        predicted.columns= self.data_columns
        predicted=self.descale(predicted)
        predicted= predicted.join(timestamp)
        predicted.rename(columns={self.metric:"forecast"},inplace=True)
        predicted=predicted[["forecast",'timestamp']].to_dict(orient="records")
        anomalies.columns = self.data_columns
        anomalies=self.descale(anomalies)
        anomalies=anomalies.join(timestamp)
        anomalies.rename(columns={self.metric:"expected"},inplace=True)
        anomalies=anomalies[["expected",'timestamp']].to_dict(orient="records")
        return  anomalies, predicted
    
    def calculate_predictions(self):
        data_file = self.data_file
        model_file = self.model_file
        self.standard_cols= ["clients", "flows", "bytes", "pkts"]
        self.minmax_cols=["minute", "weekday_0","weekday_1","weekday_2","weekday_3","weekday_4","weekday_5","weekday_6"]
        self.percentile=99.9
        temp_data = pd.json_normalize(data_file)
        temp_data=temp_data.rename(columns={"result.bytes":"bytes","result.pkts":"pkts","result.clients":"clients","result.flows":"flows"})
        data=temp_data
        timestamp = data['timestamp']
        data['minute']= pd.to_datetime(temp_data['timestamp']).dt.minute+60*pd.to_datetime(temp_data['timestamp']).dt.hour
        data['weekday'] = pd.to_datetime(temp_data['timestamp']).dt.weekday
        one_hot = pd.get_dummies(data['weekday'], prefix='weekday', prefix_sep='_')
        data = data.drop('weekday',axis = 1)
        data = data.join(one_hot)
        data.set_index("timestamp")
        data=data[data.columns.drop(["timestamp"])]
        for col in self.minmax_cols:
            if col not in data.columns:
                data[col]= 0
        self.data_columns= data.columns
        data = data.dropna()
        data=self.rescale(data)
        Xs = []
        for i in range(5, data.shape[0] ):
            Xs.append(data[i-5:i])
        data=np.array(Xs)
        model=tf.keras.models.load_model(model_file)
        predicted=model.predict(data)
        data_anomalies, predicted_anomalies = self.extract_anomalies(data, predicted)
        anomalies=predicted_anomalies
        anomalies, predicted = self.output_formatting(anomalies, predicted, timestamp)
        return  anomalies, predicted
        
class OutliersModel:
    @staticmethod
    def execute_prediction_model(data, metric, model_file):
        keras = KerasModel(data, metric, model_file)
        predictions = keras.calculate_predictions()
        return {
            "anomalies":predictions[0],
            "predicted":predictions[1],
            "status": "success"
        }
    @staticmethod
    def return_error(error="error"):
        return { "status": "error", "msg":error }
    
