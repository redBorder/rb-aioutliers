import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import json
from sktime.forecasting.sarimax import SARIMAX
import time


def read_json(ruta, frecuencia='H'):

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

def granularity_to_minutes(granularity):
    """
    Get the number of seconds for each possible druid
    granularity. For example, "pt2m" would return 120
    and "thirty_minute" would return 1800.

    Args:
        -granularity (string): druid granularity.
    Returns:
        - (int): number of seconds in the granularity.
    """
    if not isinstance(granularity, str):
        error_msg="Granularity must be a string"
        raise ValueError(error_msg)
    if len(granularity)==0:
        error_msg="Granularity must be a non-empty string"
        raise ValueError(error_msg)
    base_granularities = {
        "minute": 60, "hour": 3600, "day": 86400,
        "fifteen_minute": 900, "thirty_minute": 1800,
        "m": 60, "h": 3600, "d": 86400
    }
    granularity = granularity.lower()
    if granularity in base_granularities:
        return base_granularities[granularity]/60
    try:
        multiplier = base_granularities[granularity[-1]]
        numbers = int(''.join(filter(str.isdigit, granularity)))
    except Exception:
        error_msg='Invalid granularity'
        raise ValueError(error_msg)
    return (numbers * multiplier / 60)

def plot_forecast(y, y_pred):
  labels = ['y', 'y_pred']
  plt.figure(figsize=(10, 6)) 
  plt.plot(y.index, y.values, label=labels[0] if labels else 'y', color='blue')  # Datos históricos en azul
  plt.plot(y_pred.index, y_pred.values, label=labels[1] if labels else 'y_pred', color='red')  # Predicciones en rojo
  plt.xlabel('Fecha')
  plt.ylabel('Valor')
  plt.title('Datos Históricos vs. Predicciones')
  plt.legend()
  plt.grid(True)
  plt.tight_layout()  # Ajusta automáticamente la disposición de la gráfica para evitar superposiciones
  plt.show()



def predict(data, gran):
  print(gran)
  gran = granularity_to_minutes(gran)
  print(gran)
  y = data.iloc[-int(20160/gran):]    # últimas 2 semanas
  sp = 10080/gran
  fh = np.arange(1, 20)               # horizonte de predicción 

  y = y.interpolate(method='linear')  # interpolación lineal para imputar datos faltantes
  forecaster = SARIMAX(order=(0, 1, 0), seasonal_order=(0, 1, 1, sp))
  forecaster.fit(y)
  y_pred = forecaster.predict(fh)

  return y_pred

def __main__(file, gran, aggr):
  df = read_json(file, gran)
  print(df)
  data = df[f"result.{aggr}"]

  inicio = time.time()
  y_pred = predict(data, gran)

  fin = time.time()
  print('Time:', fin-inicio)
  plot_forecast(data, y_pred)

__main__('<file name>', '<gran>', 'bytes')
