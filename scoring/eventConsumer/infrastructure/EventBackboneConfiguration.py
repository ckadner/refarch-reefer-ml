import logging
from os import environ as env

log = logging.getLogger(__name__)
log.addHandler(logging.StreamHandler())
log.addHandler(logging.FileHandler("/var/log/app.log"))
log.setLevel(logging.INFO)

try:
    KAFKA_BROKERS = env['KAFKA_BROKERS']
except KeyError:
    log.error("The KAFKA_BROKERS environment variable needs to be set.")
    # exit

if not KAFKA_BROKERS:
    KAFKA_BROKERS = "my-cluster-kafka-bootstrap.kubeflow:9092"
    log.warning(f"default the KAFKA_BROKERS to {KAFKA_BROKERS}.")

try:
    KAFKA_APIKEY = env['KAFKA_APIKEY']
except KeyError:
    KAFKA_APIKEY = ""
    log.warning("The KAFKA_APIKEY environment variable not set... assume local deployment")


KAFKA_CERT = env.get('KAFKA_CERT','')


def getBrokerEndPoints():
    return KAFKA_BROKERS


def getEndPointAPIKey():
    return KAFKA_APIKEY


def hasAPIKey():
    return KAFKA_APIKEY != ''


def isEncrypted():
    return KAFKA_CERT != ""


def getKafkaCertificate():
    return KAFKA_CERT


def getTelemetryTopicName():
    return env.get("TELEMETRY_TOPIC", "reeferTelemetries")


def getContainerTopicName():
    return env.get("CONTAINER_TOPIC", "containers")
