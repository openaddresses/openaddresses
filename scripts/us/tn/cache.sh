#!/bin/sh

set -ex
TOKEN=$1

mkdir /work/shp
TMP=/work openaddr-esri2geojson \
    -p "token=${TOKEN}" -H 'Host: tnmap.tn.gov' \
    -H 'Referer: http://tnmap.tn.gov/assessment/' \
    http://tnmap.tn.gov/arcgis/rest/services/ADMINISTRATIVE_BOUNDARIES/LEGISLATIVE_DISTRICTS/MapServer/2 \
    /work/shp/us-tn-districts.shp

mkdir -p /work/cache/us
zip -j /work/cache/us/tn.zip /work/shp/us-tn-districts.*
