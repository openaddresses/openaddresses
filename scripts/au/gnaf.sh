#!/bin/bash

set -eu

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

# select output from tables
echo "CREATE TABLE openaddresses AS
SELECT

    TRIM(
        CASE WHEN number_first IS NOT NULL THEN number_first ||
            CASE WHEN number_last IS NOT NULL THEN '-' || number_last || ' ' ELSE ' ' END
        ELSE
            NULL
        END
    )
        AS number,

    TRIM(
        street_name ||
        CASE WHEN street_type IS NOT NULL THEN ' ' || street_type ELSE '' END ||
        CASE WHEN street_suffix IS NOT NULL THEN ' ' || street_suffix ELSE '' END
    )
        AS street,

    flat_number AS unit,
    longitude AS lon,
    latitude AS lat,
    locality_name AS city,
    locality_postcode AS postcode,
    state AS region

FROM gnaf.addresses adr;
" | psql postgres://gnafun:gnafpw@localhost/gnafdb

# copy to CSV
touch $TMP/au.csv
chmod a+w $TMP/au.csv
echo "COPY openaddresses TO '$TMP/au.csv' DELIMITER ',' CSV HEADER;" | psql -t -q postgres://gnafun:gnafpw@localhost/gnafdb

mkdir /work/cache
zip -j /work/cache/au.zip $TMP/au.csv

# clean up temporary files
/etc/init.d/postgresql stop
rm -rf $TMP
