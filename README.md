# rb-aioutliers Main package

Main package to install redborder ai outliers in Centos7

#### Platforms

- Centos 7

#### Installation

1. yum install epel-release && yum install centos-release-scl && rpm -ivh http://repo.redborder.com/redborder-repo-0.0.3-1.el7.rb.noarch.rpm

2. yum install rb-aioutliers

## Model design
Initially, data is extracted from a designated druid datasource in timeseries format, with configurable metrics and settings. After rescaling from zero to one and segmentation, an autoencoder reconstructs the data, enabling anomaly detection through k-sigma thresholding.
The anomalies are outputed in Json format together with the data reconstructed by the autoencoder.

If you cannot see the image probably you are outside of the redborder organization, probably in the future we will release this...

See [#23](https://github.com/redBorder/rb-aioutliers/pull/23)

![img](https://lh3.googleusercontent.com/fife/AK0iWDwRKtXzeZRyn9412b9OHio5ZiiiIM_Xjr33XQ0tQ-jNQDBWnzWvUweMe_ZmmDwxC2QCCNcjjC0T9NqupTZTlUMMGmd7lqitlhhhOJgfvJs2U0o2lQ2w76kt4DCk0Go4QNku-xN-1FxAePOFKGx4jdaKD9hAfBQwhLSD6dNoJl29DcZgb8C9tjWekjvBeXo_treEXwK0Ts2TaKfhHngtov641fXM42b-5qLpBt_0ARgARUKtI0mwquEe5QaeJiXqQzGWBhdWOCuI-52IZt_7TT11ksYhxCdSQFSqyBhZoRXtMJ23h1EnQeyT_tVjetXCVfe3TNgM5pWCKPdr0wKRv6P_QgfTXnukmk-lmuRSwD4IkSllCOD6COnlGrbJZCFjIzm6_hq-o8PY3o9wuT2aw0a9QvUx7FbrTZJg2bSh-pnRRSLskOHJhgd5-vn5PkHvUskKiP4ZveW32nMEDstiqxKuf2cvnFuXCFzhSHy0AQGnQHvQ2obIlyHqVObHH9x9ve50zNG7wVBtAWEmCgkxM0DPt1j9UIpiwFQ_Qz3sEGyGggrn1HYYcQsMJsW64FTuEuzCiEP9IL0dSQVWGE6B9BLR2hu47P9nZNGN2RQYLusqi05jGVxbg7vBTGSZDiLlxxFLak8DGYf0ohQhjfVbfGw1m_td74x3d6d23GWilscYyJAPQdC46W5ddRaKJWirsaZElPuiMnevCA6v-ctnNVcNn1IKDd1nMWISCVt8CzPLfss0JGnHqELz1Og_LrNl-iYYjzB5TxajeQ5sz5xLkmSVnzhQZOAo5VHr0vE256Z36Rk5a7OvpWG4Nl8U4SoYsuDI7V6Fv-wLSlVkGGZ8imYDpw6wtcp365-OzsWoRfHWWHQ9V56yfkTz_ZuG0aVA8nQpmMBop396uQMctFjgVDgrW529QhYUuo9yv6rLaWcuhjBAfxW31qEExNLnzMkJlld8v-VNAyJc7qKuT1JpUVvUTAOn1dYtHxO85iL9wga-WUOcV27FaBeklFQv3FQz8K2yiEqoltVCr14HHj--F61pSm1HC0TOwZ2x3JcI-o9QmXWh_kZ9VCCCycGhiODnLM5YwcsM-vY8uCtk4mng2_2XejdFA2RL_vKNFkQeSX_fpoZab0ekT4-UCMPFYGdh--L_se-GfJJF8Px1xtLFl9C6HcT7EsNj7WYn7lxBzSZ-IUZKA4w1st4oBIPGPGvX9_MROwPRZNHmWxYbZ0zk2OVT-iyb6GseZ1V_OBLmln0nIqDVtxW2u32Bgi38Y0jwqXc_UfQnpLzL7i0_ePaGAakS4zdbx_HwVGlru5yUyArsx9-s4fLJAwCrswmBWXO8odCFO16qPNhWTtkVTFRDWzC3v3G18LKqSoLfai0qq1zzGie06cOA2bNe9YHWxn5efVsrtez0kiRMb5Ro7gGRIt2OYMp39VfIje7aXOetmfc1Z-CT_gcKdEQpMQGBELo0xUE_qgbmTZwj7_qgG1TjPCeVUudVD0Xb5fO5r8x_L9Xv1i81WffPnSjEhy9axM_JG7QYvJ_IC0qhhVrTe7EyFmtktYADftkTSbKFif8l-BGWqucPQw04yIH44A=w1107-h975)

## Model execution
rb-aioutliers utilizes the Flask framework to create an HTTP server. Users can send Druid queries via POST requests to the /calculate endpoint. When rb-aioutliers receives the Druid query, it sends a request to the Druid broker, retrieves the necessary data, and then proceeds to execute the anomaly detection model.

![img](https://lh3.googleusercontent.com/fife/AK0iWDzo4KPabRCLUNYy9rYH6MyVZeihkZsxeJ27o9FMmKfgCr8h5HOG4o-KxfhxkITIS3a5uk1IgP344kL8bMBxi8GakpIaO9_Gwh8GNPABIpJIkn-CAoBa1pOjg3sWGPKpdc3GetxIq1PINzlbXABCxLUWUpm4EVpZymlCh7MLdP5U8wjjXw_dTLCvyRHbZ2axvNuRTDa7D-uWQ-Fw0AtdVKF66hH4otUm9x7Z6jwP-PhVRD0uZMuWY6gMEw9aoopRbCw0C9s77Y10OM9qMqx39nkQbfBSkpihBy_5CDTnrdGgLsw3JslkB8kDNl1B9_SE725tVonH3Uda2n9QmosY38rKwRonNUuDAhe8gMaXAZhrk1JACZHrzRzgS_8C3GTU8WR0y8Rx0o-aH8ZaPCU_BNPtyLfX600KPBI-va5H2p4V4uV0fH5DPFZoZp3txGSOUFNKein6AWrLHg2b6YNN5tu7ReyNDP5jgWartMd2fxY4VBC9uW2JaPMVbaexEfXO1_yYiBq-rZWYJolYl4SHWuGEAQanp6qeUPZeBBxfmPdpXsUo5Yvj6UIzCv5Pab3tqUmt7TzYWdCESdPAxjSZM37IW-uPeoaMufyBvwz7ygvDzOh66DBXuj40MQDJLcsBZpQY-RlqUT81Y0PgT-kdl-S-Ik-P27trXw2gozIE7eTfhFsLv1RQWlB8SvnpbHVdtff9iwGpjLXxyFwSgzpUwugpfvcgvHBdxBxpD6yFazrXwfM0GKjoMrijxLy06nBk5tbwLiECZbZ25Efx_OnE6zs7ucTwizKwcx4ij7cxGljIj6r4QWA_Odmk_CcAcuIB--dzmdlTIgll-Vktyh-tZaY1m4IyxtWO3E8iikQb-_ZD02RgzxUk85ufJZB7CveeL-o1MXzeq78_oMkMjb-Rlz3RN2G8OXWmSnpFNnLnSq1L7rysqZCEwoYAhAoCz_3GyX_LgelLXYwvzEF7Uf-mGR7d6PyihRjJ6jEWpRFZ2AtkoIOzuvhRMFOimUmUhezFVCy1i7aVWMBqclWTUj3qyM43rAjLAUuCRvKyTYwjDlGlbz5GVbzm5VsQ8uUgLGnRSGkjf-UHdx-Nqn7EBHHr2_YOjVSRD8wdgpp_gLymEWoBF-llMStK2GOV0LhWjkkblDQGEiFex2xTrmin3KAqkOqlMrnrfMRRSqS0WPi-IA_H_0ljXL5QPeVRmocLHqh72Xz3UnHihdLGuk9-bYXtOFw9orthABjp5PqOTl1Aw3QdwQclFHO_8X13jYhihAVGPN01IXYrmzB01l6Fz1LS5ZP4yXw9F6UUsOF8UQxD_3e7_WqJVt4mEKQZojiNPV1OTiu8GFtj1rRXMgXBv_2dIIyKXwnaQSjxRTnk-SFLXvXLxHK4oW4Uu0IS1jXnrSiOijHGeH4TG2adaHEZRM9zlv1OXepXO-V4ytXaYHasZpmFfPwj43lxyyO78r3ax_Vpp1ZR3PpXVdrTlT9oT7_0ilXbIjXTb8feminLsow0aSdXcisTWiMhvhkqpplAOh-U_XMTqZSfJpwlYm_Vcq-YRFJ_7FSGjgN69ZUAQOdkJgoRI0-rfUq-Ev0iEg=w800-h600)

After executing the model, the server can respond with one of two status messages:

`HTTP OK 200 Success`: In this case, the response body will be structured as follows:
```
{
    "status": "success",
    "anomalies": [Array_of_anomalies],
    "prediction": [Array_of_predictions]
}
```

`HTTP 500 Internal Server Error`: If there is an issue during the process, the response will contain an error message:
```
{
    "status": "error",
    "msg": "Error_description_message"
}
```

## Model training

The rb-aioutliers service generates a custom Druid query and sends it to the Redborder cluster Druid broker. After sending the query, it retrieves the data and attempts to train a model with custom parameters such as epochs or batch size. Once the model training is complete, it outputs a backup file and the generated Keras model.

![img](https://lh3.googleusercontent.com/fife/AK0iWDxKcNUlsurVY1EDmdCojOMiDBQXdL8BDpMjOMMIdfAxSp2v9IPqDXO73dWW8YY30RBYHO4CABByfWG1ma0t52bqI99fDpMeYaEynaUfIrEfAx-IdKaH96801XoJCQT6313F1o56yCisWEM5NK43FOoFY38z28dPr06-RKlknxGrEjLPUCRvrYNIpTPyRIBGo-CGOVCdY5c7rxVvBGT2IoanqxuqwJQ87dmHJNCutQl6OfV3kFgNCGGMao4HcE5_VGUfWiPAJhfQhWZ1fQMmlV68zOxYDLJVCYnEa--g4Us3Qkyy1kyZDYg9pLUnG2T7tseObfolqoMY-MRAwX7uRCTYcEHQ7cycdV8herPZ2cManSgmVIEtRlw11FAO0ylHLrJIMQZn3oYLUysY44XnSnhOESMACVEYaBjyBFdXFJBPR2ux8YZ3FUDajteAaYU1rZDdMgZWT90gl-jzGesaVP34MhuXrq1kISww2GYMtqh1nsx3dfCymlRnZYA_NejF1kv15sO_Ydzzr8Pu7EyMJMtxQUENV7tXGkAhVvR00tkSGuOFFjtT3QHhfGOGPtVyG2Sy_kYZhMuwlusH_y4RIcHrnRcXMPB5IFYqkUKRG7eCAFcYtYRJnFsAyz9Uj38jMF-huJiLGpRkRxsOrz2c_s0JIGDGzbc89P_XXmJ5wAz7xvad_0eh6o1DYUwHYPRkI_Ii1gsIltfMifA6xyXUbqvaSxnsUX5OADFVpifEcpZ5A3ZjfcONwy4-LXa6_L9YjzGzP-s1XRioyWjFV7wl3EtQuK3_xPsVoOHQQpA8ukzIe4YisEB79aXDtL4-xYxHdoR9mnnCkGOrTBJfrTT61FwKR7Cz2Kg9bXz03OgFVGQq7WJPCh7g9vub8vNyAsmkJv758Ku_M6OZ6OnglZAle43lectp066sEFEdnhseyw1Aov9b83H9m1DAeVrOLTHjiVzF3KCwed7pw6YHmmsKBRO25Tw82DylYaUUnC31ULCOu6Ie7ExkIErkaNaM63rmVZjuCQO_sXepUl31cQWjHapD4hhh4rSTWnt7Xm_ejqDKA6PS8Stk6B48EvkPST7EQTTwVMLjNnUXbrdx1aK-7yAeTazAqIaO0HeFs_hthzkHzabkRQBd_2RX5DuVFgiBLzi_44Ca97fd3aWLSze5GEnuHHv0rl3Ks8R5INEf7c-Q9RsRH30AVUWwmhiKYoDr8hycqR_5KvPj15zIDdwTBzRPJIIwyFAEGAisK8cP4M1ibTCAqL-eLcoAYzjHaNgjDCXjhhIJ9INEkwMIpmYOE7Wu_khQ_VuN6V4OeYLRbWiaU7E4xkL2R0eas5hgAktusm8ZfqRyE_PKpaqfdD_9xF9YcZdacMfu2VqzSbP9O-AiiysGBMbgC3ddfN-hX3whWX-0AggtLheSEza3-n7NSyFEK7LJK4SeyQ-M_nfWGn6RgMp2HCpARRXhdyYd7LJG0QZyWoudAS12Oo3FkQuQvxxsdCqkpwe_EcprW0F1xl-mx6Vb_HXhgeW90_QXhDBzRNLovaB6D5AM1IAx9R_O=w917-h1001)

## Docker support

If you want to run the app inside a docker container run the following commands

```bash
cd ./resources/src
docker-compose up --build -d
```

now if you list your docker container you will see the following container running.

| Container ID   | Image                    | Command                | Created         | Status         | Exposed Ports                               |
|-----------------|--------------------------|------------------------|-----------------|-----------------|---------------------------------------------|
| cb18a72ab60e   | src_rb_aioutliers_rest   | python __main__.py     | 3 minutes ago   | Up 3 minutes   | 0.0.0.0:39091->39091/tcp, :::39091->39091/tcp |


## API Endpoints

### `/calculate`

- **HTTP Method:** POST
- **Description:** Initiates anomaly detection (model execution) with a Druid query.
- **Request Body:** JSON data containing the Druid query in base64 string.

**Example Request:**
```application-x-www-form-urlencoded
POST /calculate (application-x-www-form-urlencoded)
query=base64_string
```
**Example Druid Query:**
```
{
  "dataSource": "rb_flow",
  "granularity": {
    "type": "period",
    "period": "pt1m",
    "origin": "2023-09-21T09:00:00Z"
  },
  "intervals": [
    "2023-09-21T09:00:00+00:00/2023-09-21T10:00:00+00:00"
  ],
  "filter": {
    "type": "selector",
    "dimension": "sensor_name",
    "value": "FlowSensor"
  },
  "queryType": "timeseries",
  "context": {
    "timeout": 90000,
    "skipEmptyBuckets": "true"
  },
  "limitSpec": {
    "type": "default",
    "limit": 100,
    "columns": []
  },
  "aggregations": [
    {
      "type": "longSum",
      "name": "bytes",
      "fieldName": "sum_bytes"
    }
  ],
  "postAggregations": []
}
```
**Example Respone:**
```
{
  "anomalies": [
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 36453984.6858499,
      "timestamp": "2023-09-28T07:00:00.000Z"
    },
    {
      "expected": 45825798.264862545,
      "timestamp": "2023-09-28T07:01:00.000Z"
    }
  ],
  "status": "success"
}
```

## Contributing

1. Fork the repository on Github
2. Create a named feature branch (like `add_component_x`)
3. Write your change
4. Write tests for your change (if applicable)
5. Run the tests, ensuring they all pass
6. Submit a Pull Request using Github

## License and Authors

- Miguel Álvarez Adsuara <malvarez@redborder.com>
- Pablo Rodriguez Flores <prodriguez@redborder.com>

LICENSE: AFFERO GENERAL PUBLIC LICENSE, Version 3, 19 November 2007
