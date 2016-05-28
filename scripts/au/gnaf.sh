#!/bin/bash

# requires: postgis unzip parallel curl git python-psycopg2 zip

set -eu

TMP=${TMP:-'/tmp/gnaf'}
PGUSER='postgres'
DBNAME='gnaf'
PSQL="psql -t -q -U $PGUSER $DBNAME"

# set up postgres, directories
mkdir -p $TMP/gnaf
mkdir -p $TMP/gnaf-admin
dropdb -U $PGUSER --if-exists $DBNAME
createdb -U $PGUSER $DBNAME
echo "CREATE EXTENSION postgis;" | $PSQL

# fetch data/resources
git clone git@github.com:minus34/gnaf-loader.git $TMP/gnaf-loader &
curl -s 'https://s3-ap-southeast-2.amazonaws.com/datagovau/MAY16_AdminBounds_ESRIShapefileorDBFfile_20160523140152.zip' -o $TMP/gnaf-admin.zip &
curl -s 'https://s3-ap-southeast-2.amazonaws.com/datagovau/MAY16_GNAF%2BEULA_PipeSeparatedValue_20160523140820.zip' -o $TMP/gnaf.zip &
wait
parallel "unzip -d $TMP/{} $TMP/{}.zip" ::: gnaf gnaf-admin

# find file directories
GNAF_DIR="$(find $TMP -type d | grep 'G-NAF' | grep 'Authority Code' | xargs -I {} dirname {} | head -n1)"
BOUNDARY_DIR="$(find $TMP -type d | grep -v 'Administrative Boundaries' | head -n1)"

# load data into tables
python $TMP/gnaf-loader/load-gnaf.py \
    --pguser $PGUSER \
    --pgdb $DBNAME \
    --gnaf-tables-path "$GNAF_DIR" \
    --admin-bdys-path "$BOUNDARY_DIR" \
    --raw-unlogged

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
" | $PSQL

# copy to CSV
touch $TMP/au.csv
chmod a+w $TMP/au.csv
echo "COPY openaddresses TO '$TMP/au.csv' DELIMITER ',' CSV HEADER;" | $PSQL
zip $TMP/au.zip $TMP/au.csv

# upload to S3
aws s3 cp $TMP/au.zip s3://data.openaddresses.io/cache/au.zip
