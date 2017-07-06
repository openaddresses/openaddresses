FROM ubuntu:17.04

RUN apt-get update -y && \
    apt-get install -y git curl zip unzip parallel \
                    postgresql-9.6 postgresql-9.6-postgis-2.3

COPY geonb.sh /usr/local/bin/run-cache
