import ast
import json
import logging
import pickle
import pandas as pd
import requests
import sys
import os

from os import environ as env
from pprint import pprint

if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler("/var/log/app.log"))
log.setLevel(logging.INFO)


# defaults, may not make sense here, TODO: clean up
model_name = 'maintenance-model'
model_deploy_namespace = 'model-deploy'
knative_custom_domain = 'example.com'

knative_domain_host = f"{model_name}.{model_deploy_namespace}.{knative_custom_domain}"

model_serving_metadata = env.get("MODEL_SERVING_METADATA")

if not model_serving_metadata:
    log.error("Environment variable 'MODEL_SERVING_METADATA' is not set.")
else:
    try:
        meta = json.loads(model_serving_metadata)

        if meta.get("status") and meta["status"].get("url"):
            knative_domain_host = meta["status"]["url"].lstrip("http://")
        else:
            model_name = meta["metadata"]["name"]
            model_deploy_namespace = meta["metadata"]["namespace"]
            knative_domain_host = f"{model_name}.{model_deploy_namespace}"

        log.info(f"knative_domain_host: '{knative_domain_host}'")

    except Exception as e:
        log.exception(f"Error trying to parse env variable 'MODEL_SERVING_METADATA': {model_serving_metadata}",
                      exc_info=True)


request_headers = {
    'Host': knative_domain_host,
    'Content-Type': 'application/json'
}

# this is use in case we want to have the model running on a remote server instead of using 
# the one embedded. 

kfservice_url = env.get('KFSERVICE_URL', "istio-ingressgateway.istio-system:80")
log.info(f"kfservice_url: {kfservice_url}")

scoring_url = f"http://{kfservice_url}/predict"
log.info(f"scoring_url: {scoring_url}")


class PredictService:
    '''
    Wrapper interface in front of the ML trained model
    '''
    def __init__(self,filename = "domain/model_logistic_regression.pkl"):
        self.model = pickle.load(open(filename,"rb"),encoding='latin1')

    def predict(self, metricEvent):
        """
        Predict the maintenance from the telemetry event received. The telemetry is a string of comma separated values.
        See the feature column names and order below.
        return 0 if no maintenance is needed, 1 otherwise
        """
        feature_cols = ['Temperature(celsius)','Target_Temperature(celsius)','Power','PowerConsumption','ContentType','O2','CO2','Time_Door_Open','Maintenance_Required','Defrost_Cycle']
        # Do some simple data transformation and reading to build X
        TESTDATA = StringIO(metricEvent)
        data = pd.read_csv(TESTDATA, sep=",")
        data.columns = data.columns.to_series().apply(lambda x: x.strip())
        X = data[feature_cols]
        # Return 1 if maintenance is required, 0 otherwise
        if scoring_url != '':
            column_name_mapping = {
                '': '',
                'Timestamp': 'timestamp',
                'ID': 'containerID',
                'Temperature(celsius)': 'temperature',
                'Target_Temperature(celsius)': 'target_temp',
                'Power': 'power',
                'PowerConsumption': 'accumulated_power',
                'ContentType': 'content_type',
                'O2': 'o2',
                'CO2': 'co2',
                'Time_Door_Open': 'time_door_open',
                'Maintenance_Required': 'maintenance_required',
                'Defrost_Cycle': 'defrost_level'
            }
            payload = X.rename(columns=column_name_mapping).to_dict('records')[0]
            log.info(f"POST: {scoring_url}")
            log.info(json.dumps(payload))
            response = requests.post(url=scoring_url, data=json.dumps(payload), headers=request_headers)
            log.info(response.text)
            score = ast.literal_eval(response.text)[0]  # response text is a string representation of an ndarray: '[1]'
            return score
        else:
            log.info(f"self.model.predict, data: {X}")
            return self.model.predict(X)
