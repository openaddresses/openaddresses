FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y zip unzip gdal-bin

COPY lds-nz.sh /usr/local/bin/run-cache
