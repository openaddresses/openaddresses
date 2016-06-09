FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y git curl zip unzip parallel \
                    postgresql-9.3 postgresql-9.3-postgis-2.1 \
                    python python-psycopg2

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader
RUN git --git-dir /usr/local/gnaf-loader/.git --work-tree /usr/local/gnaf-loader checkout -b openaddr a4a8227
COPY gnaf.sh /usr/local/bin/run-cache
