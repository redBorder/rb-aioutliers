# rb-aioutliers Main package

![test](https://github.com/redBorder/rb-aioutliers/actions/workflows/tests.yml/badge.svg?event=push)
![lint](https://github.com/redBorder/rb-aioutliers/actions/workflows/lint.yml/badge.svg?event=push)
![security check](https://github.com/redBorder/rb-aioutliers/actions/workflows/security.yml/badge.svg?event=push)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![codecov](https://codecov.io/gh/redBorder/rb-aioutliers/graph/badge.svg?token=ZGBCLP3865)](https://codecov.io/gh/redBorder/rb-aioutliers)
[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FredBorder%2Frb-aioutliers.svg?type=shield)](https://app.fossa.com/projects/git%2Bgithub.com%2FredBorder%2Frb-aioutliers?ref=badge_shield)

[![FOSSA Status](https://app.fossa.com/api/projects/git%2Bgithub.com%2FredBorder%2Frb-aioutliers.svg?type=large)](https://app.fossa.com/projects/git%2Bgithub.com%2FredBorder%2Frb-aioutliers?ref=badge_large)

Main package to install redborder AI outliers in Rocky Linux 9

#### Platforms

- Rocky Linux 9

## Running the example
This code shows runs the outlier detection on a mock dataset. Its recomended to use pipenv or similar to avoid overwritting dependencies.
```bash
git clone git@github.com:redBorder/rb-aioutliers.git
cd rb-aioutliers
pip install -r resources/src/requirements.txt
bash resources/src/example/run_example.sh
```
## Installation

1. yum install epel-release && rpm -ivh http://repo.redborder.com/redborder-repo-0.0.3-1.el7.rb.noarch.rpm

2. yum install rb-aioutliers

## Model design
rb-aioutliers includes two types of artificial intelligence-based models, a shallow one and deep ones. Either way, the idea in both is the same, to reconstruct a "normal" timeseries from the original and detect anomalies comparing them.

The shallow model is an static model for any kind of numerical time series, the reconstruction of the series is done by a special kind of convolution and the anomaly detection makes use of a modified isolation forest algorithm. This model is intended for doing anomaly detection over data where there is no prior information and thus its lightweight training is done in runtime.

The deep models are tensorflow-based deep learning models that automatically learn pattern in historical data based on any kind of druid filter. The reconstruction is done with an autoencoder which forces the reconstruction to loss the information of the less common patterns. Then, the anomalies are detected through regular k-sigma thresholding with mean and standard deviation recovered from previous training sessions. This training is generally expensive and should be done through the corresponding training service.

The anomalies are outputed in Json format together with the data reconstructed by the autoencoder.

## Model execution
rb-aioutliers utilizes the Flask framework to create an HTTP server. Users can send Druid queries along the desired model via POST requests to the /calculate endpoint. When rb-aioutliers receives the Druid query, it sends a request to the Druid broker, retrieves the necessary data, and then proceeds to execute the selected anomaly detection model. The request should look like this:
```
query=<base64_encoded_druid_query>&model=<base64_encoded_model_name>
```
If the model is left empty, not recognized or set as 'default' the executed model will be the shallow outliers. The druid query should use the native druid json format.
Additionaly, an user can request to perform an anomaly detection to a set of data directly. To do so, one should send a 'data' parameter instead of a 'query' parameter, this data should be a JSON with a druid timeseries response.

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

## Clusterization with Chef, Consul, AWS S3 & Redis

The rb-aioutliers service can operate in cluster mode! This is achieved by dividing the service into two components: the executor and the trainer.

# Executor

The executor service is registered in HashiCorp Consul. When the Redborder WebUI sends a request to api/v1/outliers, it will be directed to the rb-aioutliers.service, which, in turn, will redirect the request to any of the nodes running the rb-aioutliers REST server. This server will download the relevant model from S3, based on the sensor specified in the Druid query, and execute it.

![img](https://lh3.googleusercontent.com/fife/AK0iWDy8WmafImK6qwhmjyQiZXrcGEiEaS8isuI4eTTI3Wb-ulet7CSYuEQ1TFkxbdFa69pXhZAZV__DGnKdBO_ud9lTGylyBGxOYtf56CX0hdnO1-jin1K1b1Xuz2ye3vAe1CjvyxRj431Igmj1ooYP9vZijvp7Vc-RUMdjPgQ4t2och2w4K5kfOoukG-NcT34hcAa7be9sKjhPrfiTaH37VoaKfrE-h7MdK3V0dIy3syqtWEHFxHm86oYVX3NFvNK_WRzH99N8L-qPrUiVtzGHA0dJ-f90eqe5v3vg27RcQ22fz1TDvsaBifZukF8ERvd-mVdMhCYFnnDqd0ZDCNMM2oflCaEUERNHHLLSl6PPNtVxSjrQwDWjRCgNHN_cc6B0ytY58T2oETdc6_dWzj707fTnWxqppzfcMm8Uc9PB0v2QNXcRMoDLuFZIVgXTONXo1bzAaASe1rHwooC3alj9l4N47b8gJgOysxKxYYS_MoGN2Rn4mqT7Jwd3jWQDFjJgzaYQKqkBzNUZA5kjlu_9_KKnn4png21y5-IdzjizlIYepIQL3PeXrXUidLwWM2gELRCZCcrvMAO9_hnqmNBbOQUlqXwMqlOyVOP7hQ4HY5VzgfHx0lCFNxj14pMr6UPEaGAGpXWmMUawfW-d5JXGpqJK2_rGrNx9UdOoMDMT7rnEoOg1OGnsyECLDIZqQNu2X6NvxTdAFNWtnEby8kN7y1EFhGYxIYjpPVgCNE42tNIvoeoDpekRW5EXLUkwOu44n3zB_YkV3QiDDejwERZnWCHUdd_gJnpmnWOy6XPKF6JKP7wA-TSIHJLqWBgVYU0PgUJGLxsiM8gSp9rcBNp1sObRhnxvA03xcwF0wSP76JtD9Q-EirdnO0m-zlyRsyvGcZTPfuKQ1AqSnLyoqG5BjP4Pi3MZPB8bwacau5-ZaOLnowRmU7CHqfTvkt4QSyUav79yovJOqzXEhKMDgbc-JCSYcRo_4MnVSZn1i3MrkY0hfR3qvss0_3aquhJnKg-hN30h-1DOvcq3rBHph08TKPvP66jEnH4lUwPGZc0hhZ2SMFW6vfNHhewn6LOveNZvAy5uW95wownGTGHnMz3kd47E_ZRQhbshax0VTWB68_r7prfZ7mgys5IocwfteBOlmN9Hr0vfXWJvO-JkHwrVRuR0dKGbMuoPgUQH_mw5HHaQAunKRMb9kzqsW-qI_3DSdhebjuC_JAa-0FTb7XEZphL25HiZXV2jc4wjASGWqWcmpn4oJqp68yqzoxhmBbYY4dcBd3wKqBisTgOTEH8BvBIBkfxcrXn2XaF9c9kYbEHRH8aoYkFDTwrjDx069bnGGt8eAOjtebNWBPOIuWj0KoOY8IK_U9z2C-M2eGoQm0LzDWIaqErlHLfkwPYmnK8oWiLySU-1LXdPCHlpLuiq7nF-gUoYeSo2YkvtZ37ePSv02qG1NcupcWhmaPwKm85_8JMDedUDX_JJDtHGSCl7QLNnknOq-hxguxuVqPnwdYbJ7DDi8uc_WrjHuNoCCB7ULDDHkD0_DdCYJ1OwfcbEtt0UUQ1O48N0E6J96Wzr2kV8wqvx8lKpPdAg_w=w917-h1001)

# Trainer

For the training service, the Chef client will create individual configuration files for each node, which are generated based on the cookbook and templates. These configuration files specify which sensor should be trained for. The rb-aioutliers-train service will then proceed to (**take a look at Trainer jobs below**) download the appropriate model from S3 for each node. Once the training is completed, the rb-aioutliers-train service will upload the resulting trained model to S3. It's important to note that each model is unique and specific to the corresponding sensor.

![img](https://lh3.googleusercontent.com/fife/AK0iWDzJQsuEVd3J7tjtik1AVt7ebGPOP3jkyI9UlbCZH_8VdTNjdrkG0XLDaukFfSADmfMcd2TIIFs-OIU7ZS3KIq92xvgCsrvpYu15u9k4bnjYWoNFxM6Ik_ZVo6jZQL8ttjYmlBGVPrAp_Botdcm4hpFtNjgpJNVX9x0Teds-ehiSg8usn2fw_lmge5q9rvY-XL7wF-u5S46k5e7OS1tk-B3OfZb0UAatjoAQNV_oY39YqP8KOqCtdUVOVReE95ivgp3BSL8eItBlqmnnNhfn9-4Q9UyyfOPRxuXWyOLhBb7Pjr2VyGOxu5_Gk93bPqZ3JTlUqz8ZLBkB7qoKAoKTq5dKnKC47xmBUGa4z3LRBjx1Q1Eb9U4Ka1a-9k0nc7uqfDmJZzRT-hF6dGA5fYq5oZCFoNGJ3pfQnUtghMu6VpL4DSQXDGkf_AGM2nRWh4NfuVDxgr5c0h0RsI2gTs3dGLsRhUKMEMfQOsLvZtRu6UoPK7wfD3Iu_gavs27QFFKAC0r0X6NK7DE-fyVfXYEvvmE6zj8mvonmpt_00IUe5U8rceCP3AbZQATJwx4Y0FR22zhnlivJnZplOOyEVGJZ5FNMIPmmY3Z8WW7CmUOu6vjJoN57pNmNgiQA4DUt1BdEdlebvADyPZj1VheUkXqMTCF3E7PQpJWzuB6jnHe8RAp17-fgxaLlZCJeKQXzcAFJ96NuQFH-ENT8nmksx3E0C5BDhUf-nl5c5C8xAx6AEZppjJy7sT9ETVdy82xWElksin7qScLxd1U3KzzTb8Qkfu9MbBzxp-eYK0RfQ5BN6EHkhm0G_n0YcAhOoM-AT4i8ylJWfLgovoTuwu3Ds0vrJfin8FtHM3yS4qCGxZHm8WwSaBLvmGLyHA9wFaLuXt7-8DSXkMT1tz0Cvwa3X47f2ao7hlDAPW8o9hYX-PmKdknVgzUJXN4R4IUrw0qMDRYBdY7YtIooaqy2RclCnGHvSYge7KhifVOz16TeVMoErd_4KkW-UgcS9kS1srjDsnnIuiOMN5-Lzdl3KB7Hm9RIWyv2P0KcS86IxS-mE5Nd5_0QTnLbU0ronmazMxj9gFD0NIRsaTgGE0ImLTm8qDjovI472gjDikXTXT6lV1ZBE5mCrevLIftlb4xBZeY-Chk-pYxDUt6beoGe6zz1GnL9a_JopJ54xlA9E-BeEIN2QjD6SychjV6lhiuW37yT8zIFcWZSAYpCTXkj6hQSScs3-VoLcpCP-dMgIfaP6RuRaKr2RHgYZn07a3_75me8QVf9hEfLEJAvAkqvJ8GNmPEFLhmFHu9gYH3nZVipnzp5NzKmcOMplMx1Jk6TGAgB0nTFolsEKTHVH0jIPJ1m6WVOKnfXh934WX7JIaC-JfY0uI8S3T0V5Wvn4kN_BU0cpfV1-_6nBeU-jVsGXTKrtfKCp7dv-A8lLjFl8a5hZQKckoLSCph8_LCl7c427-zlpBn9g1DqIP54xI1m1Lczw5w2y5h7bS9ye-CVv91l1lRZn3NSkNPpQneaBCR1VKGYc6Jse8v4Vv5vfrOiNylEOVa6UGjSrl5AtKJD24Rzos11AxMSItJRtVz6eQmAkQ=w918-h1002)

# Trainer Jobs

The trainer job is organized through zookeeper, which divides nodes between a leader node and one or more followers. The leader job is to put training jobs in a queue where models designated in s3 for training will be queued at regular intervals. If the leader is lost for any reason, the remaining nodes will elect a new leader.

The followers, or trainers, consume from the queue and train the models. Should any follower fail during training (for example, because its trainer lost connection), the leader would notice it, requeuing the job.

![img](https://lh3.googleusercontent.com/fife/AK0iWDw5h78LX5D8lkgspzSvhWiKvl81nPJI7Cmaz1yJGvVo13PqydmNWpwVfwJ_wvtx_4xFkItgPqBFQY0ft2LaM7i_HIpO3iokK2gTlX_v7TzRuOEqz14J-DmN5PceuoxzNoaEEN6tP6XBP1eMxqI3SnF3kc8e6tv4aO9uAmQEXo6queFD4LFCzXfPmkuOrQIjtqwRfrhO8Znn5w9AOwA93wIMTyxnEPbrsSMwDNmD0lN7VNfLI5hwGcbDkV70v87-u8JhBdEbtcHFaG57jY0o9AyUzKFLJW72ZwulMLYFIqndzcMpUU3XUTM0_3U2A2C_2JvvDRmt91AFOgEN70b2fpH5Tm06wUeENAQ6d9pwdQi1ZIs8wobl4Ijhmi9R-cKo5LJYitxFcgcOHIun4Mk52Vl1fC1ErT6vJzt091lr0lAHcf4wGQDMuSoMBXtxSm4JZUi6ahxmH5Fj5n8BNFRxhJH1Pc_aW99G-OxXWL8EyjlDGwj4X9lfuWMEtFqqBgEMzX6KZuQzBLBhNLTOGIfllja5Oghhqd1HYXQHiEWnfWp02oS2O9K-Q7OYMmtm1RggoYQVHA_YDf1pXPMPx_vqoFpiZAD5_7HyTSJaWb_baq67rQazjNQTrn3ihbY-rm3YZ0YUId-8yi1Z3cf-t21uxUTACvqhaeA_TH47jJCnHs3UHrHr5pVU0_YvKZuqRla-SD9IX9lbLrdX0kdqAP3Jsf0u_bY2157ouLvs0Wryn1vs6Q7hThkuLfA6AC8hUDECO6V1IhY1o4g41oXpjjr_urr7_ubfYaIj5EEJi2HTw7pTwBM_cLXbAgdi-e4R63YMT2O15H67hVV436iMEFELjCFEd_PaZDPhI-nWGrWfca-GYm6wI44V2cijE8upM8l2lnGiup5VGaVuGvisSYQB-e2RwSZImOD5q0RGfms6Zmi6JatdJ2obOTgXtdhnvmCLfdSYItMi3ftvyjNJHmCPpVSIeepD8A_JAm5oOciBEehqOkW01Q3qIrbtWQnPMqa_LP-SxnDSaSrCQPRNnlGZ7TrMCHCXJ0y_mjh5UhUK3OOMAq5Yq89Ha7X0E-NJOf__B9YNh7Rq3A9wQpyRa8TjdoxwRpRbCh1WtaQga-znsDeJmg3gOI7irvaMA1jQmeQibLt_gFXg6ePfqJNKdof9aKwpiN9XMAtQPStbmuPpFqwopzZn5mzmkxYuV4k2Mhbsb96-Z-rU6US9l0BMPRbnmtPAeyFOi1eLkEX7Zvlzp5FwnKiweVoQyL2L7Oo80VVY5fuwHUC53wSPm1T-2mLLzcnky-xAlFmiF9t0J9MwHHKQcSugbSo8l_PWbDKnZ0jq5yKMucF0RWXrMGe7jLksv3A9eDTIwHHCTQM0xTSUjPH9QltPhbkFov9kOzRISceVeHhJjT3dxFXNeetA_Ry5PFIeC_l7XACyOh0u_ykbc6q_yNfz1iQgUpzwkRTIeSxC_b3ohCgqQIBJ7ohzqM_2KnXdIBqmsRum4C71XImCW-jDBMiOKPODAZaUq2WCD4jM_GIihD6UITbDkGAfJpkphQXP8MmGAsg80kVs1MFjoLkJcFF8IhNh_04Fow=w918-h986)

For more info about deploy with Chef Server take a look at [Outliers Cookbook](https://github.com/redBorder/cookbook-rb-aioutliers)

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
