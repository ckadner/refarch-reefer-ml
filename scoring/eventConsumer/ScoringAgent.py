from domain.predictservice import PredictService
import  json, time, os
from infrastructure.MetricsEventListener import MetricsEventListener
from infrastructure.ContainerEventsProducer import ContainerEventsProducer

'''
Scoring agent is a event consumer getting Reefer telemetry or metrics. For each event
received it assesses if there is a need to do a maintenance on this reefer due to strange
metrices
'''

predictService = PredictService()
containerEventsProducer = ContainerEventsProducer()


def assessPredictiveMaintenance(msg):
    '''
    Call back used by the event consumer to process the event. 

    Argument the message as dict / json format to preocess.
    In the case of maintenance needed, generate an event to the containers topic
    '''
    header="""Timestamp, ID, Temperature(celsius), Target_Temperature(celsius), Power, PowerConsumption, ContentType, O2, CO2, Time_Door_Open, Maintenance_Required, Defrost_Cycle"""

    print(msg['payload'])
    score = 0
    if assessDataAreValid(msg['payload']):
        metricValue = msg['payload'].replace('(','').replace(')','')
        metric = header+"\n"+metricValue
        score = predictService.predict(metric)
    print(score)
    if score == 1:
        print("Go to maintenance " + msg['containerID'])
        # TODO do not send a maintenance event if already done in the current travel.
        tstamp = int(time.time())
        data = {"timestamp": tstamp,
                "type": "ContainerMaintenance",
                "version":"1",
                "containerID":  msg['containerID'],
                "payload": {"containerID":  msg['containerID'], 
                    "type": "Reefer",
                    "status": "MaintenanceNeeded",
                    "Reason": "Predictive maintenance scoring found a risk of failure",}
                }
        containerEventsProducer.publishEvent(data,"containerID")
    

def assessDataAreValid(metricStr):
    try:
        metric = eval(metricStr)
    except json.decoder.JSONDecodeError:
        return False
    try:
        for i in range(0,9):
            float(metric[2 + i])
            
    except TypeError or ValueError:
        return False
    return True
    

def startReeferMetricsEventListener():
    print("startReeferMetricsEventListener(  groupid = reefermetricsconsumer") 
    metricsEventListener = MetricsEventListener()
    metricsEventListener.processEvents(assessPredictiveMaintenance)
    return metricsEventListener
    

if __name__ == "__main__":
    '''
    Just start the event listener
    '''
    print("Reefer Container Predictive Maintenance Scoring Agent v0.0.4")
    metricsEventListener = startReeferMetricsEventListener()
    metricsEventListener.close()
