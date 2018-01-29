FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y git chef zip

RUN git clone -b 2.x https://github.com/openaddresses/machine.git /tmp/machine && \
    cd /tmp/machine && chef/run.sh openaddr

COPY cache.sh /usr/local/bin/run-cache
