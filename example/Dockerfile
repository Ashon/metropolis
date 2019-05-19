FROM python:3.7.3

WORKDIR /opt/nats-actor

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY nats_actor ./nats_actor
COPY example ./example