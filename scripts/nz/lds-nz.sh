#!/bin/bash

# 1. Download the zip file from https://data.linz.govt.nz/layer/3353-nz-street-address/
#    into this directory
# 2. run this script
# 3. lds-dst/lds-nz-street-address-SHP.zip will contain the combined shapefile

DST_SHAPEFILE="nz-street-address.shp"

TEMP_SRC_DIR=/work/source
TEMP_DST_DIR=/work/dest

ZIP_FILENAME=`find /work -name lds-nz-street-address-SHP.zip | head -n 1`

mkdir "$TEMP_SRC_DIR"
unzip $ZIP_FILENAME -d "$TEMP_SRC_DIR"

mkdir "$TEMP_DST_DIR"

i=0
for src_file in "$TEMP_SRC_DIR"/nz-street-address/*.shp ; do
    echo "$src_file"
    if [ $i -eq 0 ] ; then
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 "$TEMP_DST_DIR/$DST_SHAPEFILE" "$src_file"
    else
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 -update -append "$TEMP_DST_DIR/$DST_SHAPEFILE" "$src_file"
    fi
    i=$(($i+1))
done

mkdir -p /work/cache/nz
zip --junk-paths /work/cache/nz/lds-nz-street-address-SHP.zip "$TEMP_DST_DIR"/*

rm -rf $TEMP_SRC_DIR $TEMP_DST_DIR
