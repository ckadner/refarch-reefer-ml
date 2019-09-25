import ast
import json
import logging
import pickle
import pandas as pd
import requests
import sys, os
if sys.version_info[0] < 3: 
    from StringIO import StringIO
else:
    from io import StringIO

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler("/var/log/app.log"))
log.setLevel(logging.INFO)


# this is use in case we want to have the model running on a remote server instead of using 
# the one embedded. 
try:
    SCORING_URL = os.environ['SCORING_URL']
    if not SCORING_URL.strip("/").endswith("/predict"):
        # TODO: use regex to get the URL right
        SCORING_URL = SCORING_URL.strip("/") + "/predict"
except KeyError:
    SCORING_URL=''  # be sure to keep it empty
    # TODO: undo this
    log.warning("no scoring URL provided, default to Tommy's first deployment")
    SCORING_URL = "http://169.45.69.227:31380/predict"

log.info(f"scoring_url: {SCORING_URL}")


# TODO: get `Host` from the pipeline outputs of the deployment task:
#   model_name='maintainance-model'
#   model_deploy_namespace='model-deploy'
#   knative_custom_domain = 'example.com'
HOST = os.environ.get("HOST", 'maintainance-model.model-deploy.example.com')

HEADERS = {
    'Host': HOST,
    'Content-Type': 'application/json'
}


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
        if SCORING_URL != '':
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
            log.info(f"POST: {SCORING_URL}")
            log.info(json.dumps(payload))
            response = requests.post(url=SCORING_URL, data=json.dumps(payload), headers=HEADERS)
            log.info(response.text)
            score = ast.literal_eval(response.text)[0]  # response text is a string representation of an ndarray: '[1]'
            return score
        else:
            log.info(f"self.model.predict, data: {X}")
            return self.model.predict(X)
