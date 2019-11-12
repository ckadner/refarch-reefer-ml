from flask import Flask, request, jsonify, abort
import os, time
from datetime import datetime
from infrastructure.MetricsEventsProducer import MetricsEventsProducer 
from domain.reefer_simulator import ReeferSimulator

VERSION = "Reefer Container simulator v0.0.6 10/09"
application = Flask(__name__)

metricsProducer = MetricsEventsProducer()

@application.route("/")
def hello():
    return VERSION
    
@application.route("/control", methods = ['POST'])
def runSimulator():
    print("post received: ")
    print(request.json)
    if not 'containerID' in request.json:
        abort(400) 
    control = request.json
    simulator = ReeferSimulator()
    if control["simulation"] == ReeferSimulator.SIMUL_POWEROFF:
        metrics=simulator.generatePowerOffTuples(control["containerID"],int(control["nb_of_records"]),control["product_id"])
    elif control["simulation"] == ReeferSimulator.SIMUL_CO2:
        metrics=simulator.generateCo2Tuples(control["containerID"],int(control["nb_of_records"]),control["product_id"])
    elif control["simulation"] == ReeferSimulator.SIMUL_O2:
        metrics=simulator.generateO2Tuples(control["containerID"],int(control["nb_of_records"]),control["product_id"])
    elif control["simulation"] == ReeferSimulator.MAINTENANCE:
        print("sending 1 maintenance record")
        metrics = [f"('{control['containerID']}', '2019-10-09T23:51:20.137127000', '{control['product_id']}', 15.21328744, 3.0, 19.84017345, 3.442838, 0.84450906, 2, 6, 10.62306835, 79.39353212, 80.58489227, 14.92076336, False, False, False, 6)",]
    else:
        return "Wrong simulation controller data"
    
    for metric in metrics:
        evt = {"containerID": control["containerID"],
                "timestamp": str(metric[0]),
                "type":"ReeferTelemetries",
                "payload": str(metric)}
        metricsProducer.publishEvent(evt,"containerID")
    return "Simulation started"
    

if __name__ == "__main__":
    print(VERSION)
    application.run()
