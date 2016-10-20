#!/bin/sh

set -ex
TOKEN=$1

mkdir /work/shp
TMP=/work openaddr-esri2geojson \
    -p "token=${TOKEN}" -H 'Host: gisweb.co.bucks.pa.us' \
    -H 'Referer: https://gisweb.co.bucks.pa.us/apps/floodplainviewer/' \
    https://gisweb.co.bucks.pa.us/arcgis/rest/services/Assessment/PropertyRecords/MapServer/7 \
    /work/shp/us-pa-bucks-parcels.geojson -v

mkdir -p /work/cache/us/pa
zip -j /work/cache/us/pa/bucks.zip /work/shp/us-pa-bucks-parcels.*
