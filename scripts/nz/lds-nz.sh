#!/bin/bash

# 1. Download the zip file from https://data.linz.govt.nz/layer/779-nz-street-address-electoral/
#    into this directory
# 2. run this script
# 3. lds-dst/lds-nz-street-address-electoral-SHP.zip will contain the combined shapefile

DST_SHAPEFILE="nz-street-address-electoral.shp"

TEMP_SRC_DIR=lds-src
TEMP_DST_DIR=lds-dst

ZIP_FILENAME=lds-nz-street-address-electoral-SHP.zip

mkdir -p "$TEMP_SRC_DIR"
unzip $ZIP_FILENAME -d "$TEMP_SRC_DIR"

mkdir -p "$TEMP_DST_DIR"

i=0
for src_file in "$TEMP_SRC_DIR"/nz-street-address-electoral/*.shp ; do
    echo "$src_file"
    if [ $i -eq 0 ] ; then
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 "$TEMP_DST_DIR/$DST_SHAPEFILE" "$src_file"
    else
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 -update -append "$TEMP_DST_DIR/$DST_SHAPEFILE" "$src_file"
    fi
    i=$(($i+1))
done

zip --junk-paths "$TEMP_DST_DIR/$ZIP_FILENAME" "$TEMP_DST_DIR"/*
