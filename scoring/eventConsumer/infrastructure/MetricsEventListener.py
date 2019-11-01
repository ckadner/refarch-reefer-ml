import datetime
import json
import logging
import infrastructure.EventBackboneConfiguration as EventBackboneConfiguration

from confluent_kafka import Consumer, KafkaError
from datetime import datetime

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler("/var/log/app.log"))
log.setLevel(logging.INFO)


class MetricsEventListener:

    def __init__(self):
        self.kafka_auto_commit = True
        # self.prepareConsumer(group_id=datetime.now().strftime('group-%Y%m%d-%H%M%S'))
        self.prepareConsumer(group_id="reefermetricsconsumer")

    # See https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    def prepareConsumer(self, group_id="reefermetricsconsumer"):
        options ={
            'bootstrap.servers':  EventBackboneConfiguration.getBrokerEndPoints(),
            'group.id': group_id,
            'auto.offset.reset': 'earliest',
            'enable.auto.commit': self.kafka_auto_commit,
        }
        if (EventBackboneConfiguration.hasAPIKey()):
            options['security.protocol'] = 'SASL_SSL'
            options['sasl.mechanisms'] = 'PLAIN'
            options['sasl.username'] = 'token'
            options['sasl.password'] = EventBackboneConfiguration.getEndPointAPIKey()
        if (EventBackboneConfiguration.isEncrypted()):
            options['ssl.ca.location'] = EventBackboneConfiguration.getKafkaCertificate()
        log.info(options)
        self.consumer = Consumer(options)
        self.consumer.subscribe([EventBackboneConfiguration.getTelemetryTopicName()])
    
    def traceResponse(self, msg):
        msgStr = msg.value().decode('utf-8')
        log.info('@@@ pollNextEvent {} partition: [{}] at offset {} with key {}:\n\tvalue: {}'
                 .format(msg.topic(), msg.partition(), msg.offset(), str(msg.key()), msgStr))
        return msgStr

    def processEvents(self, callback):
        gotIt = False
        anEvent = {}
        while not gotIt:
            msg = self.consumer.poll(timeout=10.0)
            if msg is None:
                continue
            if msg.error():
                log.error("Consumer error: {}".format(msg.error()))
                if ("PARTITION_EOF" in msg.error()):
                    gotIt= True
                continue
            msgStr = self.traceResponse(msg)
            try:
                anEvent = json.loads(msgStr)
                gotIt = callback(anEvent)  # TODO assessPredictiveMaintenance(msg) does not return anything
            except:
                log.exception(f"Got exception processing the msg: {msg}")
    
    def close(self):
        self.consumer.close()