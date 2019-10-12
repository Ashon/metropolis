FROM python:3.7.3-alpine

WORKDIR /opt/nats-worker

RUN apk add --no-cache --virtual .build-base \
  build-base

COPY ./requirements.txt ./
RUN pip install -r requirements.txt

COPY nats_worker ./nats_worker
COPY example/app ./app
