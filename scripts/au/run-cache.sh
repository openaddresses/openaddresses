#!/bin/bash

set -eux

# set up postgres, directories
TMP=/work/tmp
mkdir $TMP
mkdir $TMP/gnaf $TMP/gnaf-admin $TMP/tablespace
chown postgres:postgres $TMP/tablespace

/etc/init.d/postgresql start 
sudo -u postgres psql -c "CREATE USER gnafun WITH CREATEUSER PASSWORD 'gnafpw'"
sudo -u postgres psql -c "CREATE TABLESPACE gnafts OWNER gnafun LOCATION '$TMP/tablespace'"
sudo -u postgres psql -c 'CREATE DATABASE gnafdb OWNER gnafun TABLESPACE gnafts'
sudo -u postgres psql -c 'CREATE EXTENSION postgis'

# fetch data/resources
curl -s 'https://s3-ap-southeast-2.amazonaws.com/datagovau/FEB16_AdminBounds_ESRI.zip' -o $TMP/gnaf-admin.zip &
curl -s 'https://s3-ap-southeast-2.amazonaws.com/datagovau/FEB16_GNAF%2BEULA_PipeSeparatedValue_20160222170142.zip' -o $TMP/gnaf.zip &
wait
parallel "unzip -d $TMP/{} $TMP/{}.zip" ::: gnaf gnaf-admin

# find file directories
GNAF_DIR="$(find $TMP -type d | grep 'G-NAF' | grep 'Authority Code' | xargs -I {} dirname {} | head -n1)"
BOUNDARY_DIR="$(find $TMP -type d | grep 'AdminBounds_ESRI' | grep -v 'Administrative Boundaries' | head -n1)"

# load data into tables
python /usr/local/gnaf-loader/load-gnaf.py \
    --pguser gnafun --pgdb gnafdb --pgpassword gnafpw \
    --gnaf-tables-path "$GNAF_DIR" \
    --admin-bdys-path "$BOUNDARY_DIR"

