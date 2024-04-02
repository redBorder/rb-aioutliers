
##################################################
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from sktime.forecasting.sarimax import SARIMAX
from sktime.forecasting.arima import ARIMA
from sktime.forecasting.arima import AutoARIMA
from sktime.forecasting.naive import NaiveForecaster


def read_json(ruta, frecuencia):

  # ruta: ruta del archivo json

  with open(ruta) as f:
    data = json.load(f)

  # Use pd.json_normalize to normalize the JSON data
  df = pd.json_normalize(data)

  # Convertir la columna "timestamp" a tipo datetime
  df['timestamp'] = pd.to_datetime(df['timestamp'])

  # Eliminar la información de la zona horaria de la columna "timestamp"
  df['timestamp'] = df['timestamp'].dt.tz_localize(None)

  # Pasar la columna "timestamp" al índice del DataFrame
  df.set_index('timestamp', inplace=True)

  # Especificar la frecuencia del índice según la granularidad elegida
  df = df.asfreq(frecuencia)  # Rellena con datos NaN si falta algún tiempo

  return df


def predict(y, time_pred, granularidad):

  #specifying forecasting horizon
  fh = np.arange(1, time_pred)

  #fixing seasonality
  #sp = int(43800/int(granularidad)) # seasonality period = 1 month
  sp = int(7*24*60/int(granularidad)) # seasonality period = 1 week

  # specifying the forecasting algorithm
  forecaster = NaiveForecaster(strategy="mean", sp=sp)

  #fitting the forecaster
  forecaster.fit(y)

  #querying predictions
  y_pred = forecaster.predict(fh)

  return y_pred


def plot_forecast(y, y_pred):
  labels = ['y', 'y_pred']
  plt.figure(figsize=(10, 6))
  plt.plot(y.index, y.values, label=labels[0] if labels else 'y', linewidth=0.1, color='blue')  # Datos históricos en azul
  plt.plot(y_pred.index, y_pred.values, label=labels[1] if labels else 'y_pred', linewidth=0.1, color='red')  # Predicciones en rojo
  plt.xlabel('Fecha')
  plt.ylabel('Valor')
  plt.title('Datos Históricos vs. Predicciones')
  plt.legend()
  plt.grid(True)
  plt.tight_layout()  # Ajusta automáticamente la disposición de la gráfica para evitar superposiciones
  plt.show()

gran=1
time_pred = 6000
df = read_json(f'/home/bhcaceres/Downloads/data_{gran}.json', f'{gran}T')
print(df)
y = df['result.bytes'].iloc[:24000]

y_pred = predict(y, time_pred,gran)
plot_forecast(y, y_pred)