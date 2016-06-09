FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y git curl unzip parallel python python-psycopg2 \
                    postgresql-9.3 postgresql-9.3-postgis-2.1

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader
COPY run-cache.sh /usr/local/bin/run-cache
