#!/bin/bash

# 1. Download the zip file from https://data.linz.govt.nz/layer/3353-nz-street-address/
#    into the /work directory
# 2. run this script
# 3. lds-dst/lds-nz-street-address-SHP.zip will contain the processed shapefile


DST_SHAPEFILE="nz-street-address.shp"

TEMP_SRC_DIR=/work/source
TEMP_SRC2_DIR=/work/source2
TEMP_DST_DIR=/work/dest

ZIP_FILENAME=`find /work -name lds-nz-street-address-SHP.zip | head -n 1`

mkdir "$TEMP_SRC_DIR"
unzip $ZIP_FILENAME -d "$TEMP_SRC_DIR"

mkdir "$TEMP_DST_DIR"

i=0
for src_file in "$TEMP_SRC_DIR"/nz-street-address/*.shp ; do
    echo "$src_file"
    if [ $i -eq 0 ] ; then
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 "$TEMP_SRC2_DIR/$DST_SHAPEFILE" "$src_file"
    else
        ogr2ogr -t_srs EPSG:4326 --config SHAPE_ENCODING UTF-8 -update -append "$TEMP_SRC2_DIR/$DST_SHAPEFILE" "$src_file"
    fi
    i=$(($i+1))
done

# Use Stats NZ Territorial Authority boundaries as district
# Use Stats NZ Regional Council boundaries as region
# per https://github.com/openaddresses/openaddresses/pull/2161#issuecomment-302059696
wget -O $TEMP_SRC_DIR/statsnz-digital-boundaries.zip 'http://www3.stats.govt.nz/digitalboundaries/annual/ESRI_Shapefile_2017_Digital_Boundaries_High_Def_12_Mile.zip'
unzip $TEMP_SRC_DIR/statsnz-digital-boundaries.zip -d "$TEMP_SRC_DIR"

# convert to WGS 84 for the upcoming spatial join to work
ogr2ogr -t_srs EPSG:4326 $TEMP_SRC2_DIR/REGC.shp "$TEMP_SRC_DIR/2017 Digital Boundaries High Def 12 Mile/REGC2017_HD_Full.shp"
ogr2ogr -t_srs EPSG:4326 $TEMP_SRC2_DIR/TA.shp "$TEMP_SRC_DIR/2017 Digital Boundaries High Def 12 Mile/TA2017_HD_Full.shp"

ogr2ogr "$TEMP_DST_DIR/lds-nz-street-address.shp" --config SHAPE_ENCODING UTF-8 --config OGR_SQLITE_CACHE 2000 /work/lds-nz.vrt -dialect 'sqlite' -sql 'SELECT addr.*, ta.TA2017, ta.TA2017_NAM, rc.REGC2017, rc.REGC2017_N FROM "nz-street-address" addr, TA ta, REGC rc WHERE ST_Intersects(addr.geometry, ta.geometry) AND ST_Intersects(addr.geometry, rc.geometry) AND ta.rowid IN (SELECT rowid FROM SpatialIndex WHERE f_table_name = "TA" AND search_frame = addr.geometry) AND rc.rowid IN (SELECT rowid FROM SpatialIndex WHERE f_table_name = "REGC" AND search_frame = addr.geometry)'

mkdir -p /work/cache/nz
zip --junk-paths /work/cache/nz/lds-nz-street-address-SHP.zip "$TEMP_DST_DIR"/*

rm -rf $TEMP_SRC_DIR $TEMP_DST_DIR
