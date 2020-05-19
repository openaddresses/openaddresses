FROM ubuntu:18.04

RUN apt-get update -y && \
    apt-get install -y sudo git curl zip unzip parallel \
                    postgresql-10 postgresql-10-postgis-2.4 postgis \
                    python python-psycopg2

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader && \
    git --git-dir /usr/local/gnaf-loader/.git --work-tree /usr/local/gnaf-loader checkout -b openaddr 382e740

COPY gnaf.sh /usr/local/bin/run-cache
