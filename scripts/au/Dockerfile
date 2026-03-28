FROM debian:forky

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y && \
    apt-get install -y sudo git curl zip unzip parallel \
                    postgresql-18 postgresql-18-postgis-3 postgis \
                    python3 python3-psycopg

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader && \
    git --git-dir /usr/local/gnaf-loader/.git --work-tree /usr/local/gnaf-loader checkout -b openaddr 95938f0

COPY gnaf.sh /usr/local/bin/run-cache
