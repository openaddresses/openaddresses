#!/bin/bash

# requires: postgis unzip parallel curl git python-psycopg2 zip

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

# fetch data/resources, cached from:
# http://data.gov.au/dataset/bdcf5b09-89bc-47ec-9281-6b8e9ee147aa/resource/53c24b8e-4f55-4eed-a189-2fc0dcca6381/download/feb17adminboundsesrishapefileordbffile.zip
# http://data.gov.au/dataset/19432f89-dc3a-4ef3-b943-5326ef1dbecc/resource/99b44dff-4e84-4cb7-9cbf-a68d3ebf964a/download/feb17-gnaf-pipeseperatedvalue.zip
curl -s 'http://s3.amazonaws.com/data.openaddresses.io/cache/au/gnaf-admin-feb2017.zip' -o $TMP/gnaf-admin.zip &
curl -s 'http://s3.amazonaws.com/data.openaddresses.io/cache/au/gnaf-feb2017.zip' -o $TMP/gnaf.zip &
wait
parallel "unzip -d $TMP/{} $TMP/{}.zip" ::: gnaf gnaf-admin

# find file directories
GNAF_DIR="$(find $TMP -type d | grep 'G-NAF' | grep 'Authority Code' | xargs -I {} dirname {} | head -n1)"
BOUNDARY_DIR="$(find $TMP -type d | grep -v 'Administrative Boundaries' | head -n1)"

# load data into tables
python /usr/local/gnaf-loader/load-gnaf.py \
    --pguser gnafun --pgdb gnafdb --pgpassword gnafpw \
    --no-boundary-tag \
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
    state AS region,

    (
        CASE geocode_type WHEN 'BUILDING CENTROID' THEN 1 -- rooftop
                          WHEN 'FRONTAGE CENTRE SETBACK' THEN 2 -- interpolation
                          WHEN 'GAP GEOCODE' THEN 4 -- interpolation
                          WHEN 'LOCALITY' THEN 4 -- interpolation
                          WHEN 'PROPERTY ACCESS POINT SETBACK' THEN 3 -- driveway
                          WHEN 'PROPERTY CENTROID' THEN 2 -- parcel
                          WHEN 'PROPERTY CENTROID MANUAL' THEN 2 -- parcel
                          WHEN 'STREET LOCALITY' THEN 4 -- interpolation
                          ELSE 5 -- unknown
        END
    )
    AS accuracy

FROM gnaf.addresses adr;
" | psql postgres://gnafun:gnafpw@localhost/gnafdb

# copy to CSV
touch $TMP/au.csv
chmod a+w $TMP/au.csv
echo "COPY openaddresses TO '$TMP/au.csv' DELIMITER ',' CSV HEADER;" | psql -t -q postgres://gnafun:gnafpw@localhost/gnafdb

mkdir /work/cache
zip -j /work/cache/au-feb2017.zip $TMP/au.csv

# clean up temporary files
/etc/init.d/postgresql stop
rm -rf $TMP
