# Use an official Python runtime as a parent image
# FROM python:3.7-slim
FROM python:3.7-stretch

# Set the working directory to /listener

RUN mkdir -p listener
WORKDIR /listener
COPY requirements.txt /listener

# Install any needed packages specified in requirements.txt
RUN pip install --trusted-host pypi.python.org -r requirements.txt

# Define the environment variables
ENV KAFKA_BROKERS my-cluster-kafka-bootstrap.kubeflow:9092
ENV KAFKA_ENV LOCAL
ENV KAFKA_API ""

# make sure we get logs streamed right away
ENV PYTHONUNBUFFERED 0

# Copy the current directory contents into the container at /app
COPY . /listener

ENTRYPOINT ["python"]
CMD ["-u", "ScoringAgent.py"]
