# Run the solution locally for development purpose

## Build each images

* For simulator as web application:

    ```
    cd simulator
    docker build . -t ibmcase/reefersimulator
    cd ..
    ```

* For container tracer

    ```
    cd consumer
    docker build . -t ibmcase/containerconsumer
    cd ..
    ```

* For scoring as web app
    ```
    cd scoring/webapp
    docker build . -t ibmcase/predictivescoringweb
    cd -
    ```

* For scoring as kafka listener and producer
    ```
    cd scoring/eventConsumer
    docker build . -t ckadner/predictivescoring:v0.0.5
    cd -
    ```

## Running the solution locally

* Start the kafka and zookeeper

Under the docker folder
```
docker-compose -f docker/backbone-compose.yml up &
```

* The first time you start kafka add the different topics needed for the solution:

```
# does not work, setenv may not be right
# ./scripts/createTopics.sh LOCAL

# manually:
export KAFKA_INTERNAL_PATH="/opt/bitnami/kafka/"
export KAFKA_ENV=LOCAL
kafka=$(docker ps -a | grep docker_kafka | awk '{print $NF}')
docker exec -ti $kafka /bin/bash -c "$KAFKA_INTERNAL_PATH/bin/kafka-topics.sh --create  --zookeeper zookeeper1:2181 --replication-factor 1 --partitions 1 --topic containers"
docker exec -ti $kafka /bin/bash -c "$KAFKA_INTERNAL_PATH/bin/kafka-topics.sh --create  --zookeeper zookeeper1:2181 --replication-factor 1 --partitions 1 --topic containerMetrics"
docker exec -ti $kafka /bin/bash -c "$KAFKA_INTERNAL_PATH/bin/kafka-topics.sh --list    --zookeeper zookeeper1:2181"
```

* Start the solution 

```
docker-compose -f docker/solution-compose.yml up &
```

* To stop and clean everything

```
docker-compose -f docker/solution-compose.yml down
docker-compose -f docker/backbone-compose.yml down
```

* You can also remove the kafka1 and zookeeper1 folders under docker. If you do so be sure to recreate the topics.

## Testing the solution

* Send a simulation control json to the simulator: under the `scripts` folder

```
./sendSimulControl.sh localhost:8080 co2sensor C101
```

