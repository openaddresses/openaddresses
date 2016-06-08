FROM ubuntu:14.04

RUN apt-get update -y && \
    apt-get install -y git curl python python-psycopg2 \
                    postgresql-9.3 postgresql-9.3-postgis-2.1

RUN git clone https://github.com/minus34/gnaf-loader.git /usr/local/gnaf-loader

RUN cp /etc/postgresql/9.3/main/pg_hba.conf /etc/postgresql/9.3/main/pg_hba.conf.orig && \
    echo 'local   all             all                                     trust' > /etc/postgresql/9.3/main/pg_hba.conf && \
    echo 'host    all             all             127.0.0.1/32            trust' >> /etc/postgresql/9.3/main/pg_hba.conf && \
    echo 'host    all             all             ::1/128                 trust' >> /etc/postgresql/9.3/main/pg_hba.conf

RUN /etc/init.d/postgresql start && \
    sudo -u postgres createuser --superuser gnaf && \
    sudo -u postgres createdb --owner gnaf gnaf && \
    sudo -u postgres psql -c 'CREATE EXTENSION postgis' gnaf
