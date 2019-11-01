import json
import logging
import requests
import time

from domain.predictservice import PredictService
from infrastructure.MetricsEventListener import MetricsEventListener
from infrastructure.ContainerEventsProducer import ContainerEventsProducer
from os import environ as env

'''
Scoring agent is a event consumer getting Reefer telemetry or metrics. For each event
received it assesses if there is a need to do a maintenance on this reefer due to strange
metrics
'''

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler("/var/log/app.log"))
log.setLevel(logging.INFO)

predictService = PredictService()
containerEventsProducer = ContainerEventsProducer()


def assessPredictiveMaintenance(msg):
    '''
    Call back used by the event consumer to process the event. 

    Argument the message as dict / json format to preocess.
    In the case of maintenance needed, generate an event to the containers topic
    '''
    header = """container_id, timestamp, product_id, temperature, target_temperature, ambiant_temperature, kilowatts, time_door_open, content_type, defrost_cycle, oxygen_level, nitrogen_level, humidity_level, carbon_dioxide_level, vent_1, vent_2, vent_3, maintenance_required"""

    log.info(msg['payload'])
    score = 0
    if assessDataAreValid(msg['payload']):
        metricValue = msg['payload'].replace('(','').replace(')','')
        metric = header+"\n"+metricValue
        score = predictService.predict(metric)
    log.info(score)
    if score == 1:
        log.info("Go to maintenance " + msg['containerID'])
        # TODO do not send a maintenance event if already done in the current travel.
        # This will lead to a stateful agent...
        tstamp = int(time.time())
        data = {"timestamp": tstamp,
                "type": "ContainerMaintenance",
                "version":"1",
                "containerID":  msg['containerID'],
                "payload": {
                    "containerID":  msg['containerID'],
                    "type": "Reefer",
                    "status": "MaintenanceNeeded",
                    "Reason": "Predictive maintenance scoring found a risk of failure",}
                }
        containerEventsProducer.publishEvent(data,"containerID")
    

def assessDataAreValid(metricStr):
    try:
        metric = eval(metricStr)
    except json.decoder.JSONDecodeError:
        log.error(f"Unable to decode metricStr: {metricStr}")
        return False
    try:
        for i in range(0,9):
            float(metric[3 + i])
    except TypeError or ValueError:
        return False
    return True
    

def startReeferMetricsEventListener():
    log.info("startReeferMetricsEventListener TODO without no groupid (!= reefermetricsconsumer)")
    metricsEventListener = MetricsEventListener()
    metricsEventListener.processEvents(assessPredictiveMaintenance)
    return metricsEventListener
    

def slack_me(msg="Hello ScoringAgent"):
    requests.post(url="https://hooks.slack.com/services/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",
                  headers={"Content-type": "application/json"},
                  json={"text": msg})


if __name__ == "__main__":
    '''
    Just start the event listener
    '''
    version = "v0.0.9"
    slack_me(f"Deployed Reefer Scoring Agent {version} on {env.get('HOSTNAME')}")
    log.info(f"Reefer Container Predictive Maintenance Scoring Agent {version}")
    metricsEventListener = startReeferMetricsEventListener()
    metricsEventListener.close()
