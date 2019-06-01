FROM python:3.7.3

WORKDIR /opt/nats-worker

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY nats_worker ./nats_worker
COPY example ./example