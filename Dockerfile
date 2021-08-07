FROM ubuntu:20.04

ENV HOST 0.0.0.0
ENV PORT 80
ENV DEBUG 0

RUN apt-get update && \
    apt-get install -y python3 python3-pip libpq-dev && \
    mkdir -p /opt/app

WORKDIR /opt/app
COPY . .
RUN pip install -r requirements.txt && \
    ./localization.sh

CMD python3 application.py
