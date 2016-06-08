FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y git curl python python-psycopg2 \
                    postgresql-9.3 postgresql-9.3-postgis-2.1

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader

RUN /etc/init.d/postgresql start && \
    sudo -u postgres psql -c "CREATE USER gnaf WITH CREATEUSER PASSWORD 'gnaf'" && \
    sudo -u postgres psql -c 'CREATE DATABASE gnaf OWNER gnaf' && \
    sudo -u postgres psql -c 'CREATE EXTENSION postgis' gnaf
