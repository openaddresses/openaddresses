#!/bin/bash

# requires: postgis unzip parallel curl git python-psycopg2 zip

set -eu

# set up postgres, directories
TMP=/work/tmp
mkdir $TMP
mkdir $TMP/gnaf $TMP/gnaf-admin $TMP/tablespace
chown postgres:postgres $TMP/tablespace

echo "local	all	all			trust" > /etc/postgresql/15/main/pg_hba.conf
echo "host	all	all	127.0.0.1/32	trust" >> /etc/postgresql/15/main/pg_hba.conf
echo "host	all	all	::1/128		trust" >> /etc/postgresql/15/main/pg_hba.conf

/etc/init.d/postgresql start
sudo -u postgres psql -c "CREATE USER gnafun WITH SUPERUSER PASSWORD 'gnafpw'"
sudo -u postgres psql -c "CREATE TABLESPACE gnafts OWNER gnafun LOCATION '$TMP/tablespace'"
sudo -u postgres psql -c 'CREATE DATABASE gnafdb OWNER gnafun TABLESPACE gnafts'
sudo -u postgres psql -c 'CREATE EXTENSION postgis' -U gnafun gnafdb

# fetch data/resources, cached from:
## https://data.gov.au/data/dataset/geoscape-administrative-boundaries
## https://data.gov.au/data/dataset/geocoded-national-address-file-g-naf
curl --retry 10 --location 'https://data.gov.au/data/dataset/bdcf5b09-89bc-47ec-9281-6b8e9ee147aa/resource/ae917daa-9291-4534-b97f-0d6e39ed215b/download/aug24_adminbounds_gda_94_shp.zip' -o $TMP/gnaf-admin.zip
curl --retry 10 --location 'https://data.gov.au/data/dataset/19432f89-dc3a-4ef3-b943-5326ef1dbecc/resource/d7bb4fbe-6a54-432b-b164-ec4f42732a08/download/g-naf_aug24_allstates_gda94_psv_1016.zip' -o $TMP/gnaf.zip
parallel "unzip -d $TMP/{} $TMP/{}.zip" ::: gnaf gnaf-admin
rm -f $TMP/gnaf.zip $TMP/gnaf-admin.zip

#parallel "unzip -n -d $TMP/gnaf-admin/AdminBounds {}" ::: $TMP/gnaf-admin/*/*.zip
#mv --no-clobber $TMP/gnaf-admin/AdminBounds/*/* $TMP/gnaf-admin/AdminBounds/

# find file directories
GNAF_DIR="$(find $TMP -type d | grep 'G-NAF' | grep 'Authority Code' | xargs -I {} dirname {} | head -n1)"
BOUNDARY_DIR="$(find $TMP -type d | grep 'AdminBounds' | head -n1 | xargs -I {} dirname {})"

# load data into tables
python3 /usr/local/gnaf-loader/load-gnaf.py \
    --pguser gnafun --pgdb gnafdb --pgpassword gnafpw \
    --gnaf-schema gnaf \
    --gnaf-tables-path "$GNAF_DIR" \
    --admin-bdys-path "$BOUNDARY_DIR" \
    --raw-unlogged \
    --no-boundary-tag

rm -rf $TMP/gnaf $TMP/gnaf-admin

# select output from tables
echo "CREATE TABLE openaddresses AS
SELECT

    gnaf_pid AS id,

    TRIM(
        CASE WHEN number_first IS NOT NULL THEN number_first ||
            CASE WHEN number_last IS NOT NULL THEN '-' || number_last || ' ' ELSE ' ' END
        ELSE
            CASE WHEN lot_number IS NOT NULL THEN 'LOT ' || lot_number ELSE NULL END
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

# clean up temporary files
/etc/init.d/postgresql stop
rm -rf $TMP/tablespace

# zip CSV
mkdir /work/cache
zip -j /work/cache/au-aug2024.zip $TMP/au.csv

rm -rf $TMP
