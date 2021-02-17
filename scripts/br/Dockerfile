FROM osgeo/gdal:ubuntu-small-latest

ENV HOME=/home/cnefe
COPY ./ $HOME/
WORKDIR $HOME

RUN apt-get update \
    && apt-get install -y wget python3 python3-pip \
    && pip3 install -r requirements.txt
