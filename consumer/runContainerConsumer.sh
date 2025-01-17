#!/bin/bash

source ../scripts/setenv.sh
docker run -e KAFKA_BROKERS=$KAFKA_BROKERS \
    -e KAFKA_APIKEY=$KAFKA_APIKEY \
    -e KAFKA_ENV=$KAFKA_ENV \
    -ti ibmcase/containerconsumer \
    bash -c "export PYTHONPATH=/server && python TraceContainerEventsApp.py $1"
