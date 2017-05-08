#!/bin/bash
folder="${1}"

echo -n "START:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"
echo Making CSVs from shapefiles within ${folder}:

#cd ${folder}

echo Working in $PWD
stat -c '%y' ${folder}HS/SI.GURS.RPE.PUB.HS.shp  | cut -d' ' -f1 > ${folder}timestamp.txt

# http://gis.stackexchange.com/questions/85028/dissolve-aggregate-polygons-with-ogr2ogr-or-gpc
ogr2ogr -t_srs "EPSG:4326" -f CSV ${folder}addresses-noname.csv ${folder}HS/ -lco GEOMETRY=AS_XY -lco WRITE_BOM=YES -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT geometry,
		LABELA as number,
		UL_MID,
		NA_MID,
		OB_MID,
		PO_MID,
		PT_MID
	FROM 'SI.GURS.RPE.PUB.HS' WHERE STATUS ='V'" \
 -nln addresses-noname

# Street names
ogr2ogr -f CSV ${folder}street-names-cp1250.csv ${folder}UL/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT UL_MID, UL_UIME FROM 'SI.GURS.RPE.PUB.UL'"
iconv -f CP1250 -t UTF8 ${folder}street-names-cp1250.csv -o ${folder}street-names.csv
rm ${folder}street-names-cp1250.csv

# City names
ogr2ogr -f CSV ${folder}city-names-cp1250.csv ${folder}NA/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT NA_MID, NA_UIME FROM 'SI.GURS.RPE.PUB.NA'"
iconv -f CP1250 -t UTF8 ${folder}city-names-cp1250.csv -o ${folder}city-names.csv
rm ${folder}city-names-cp1250.csv

# Commune names
ogr2ogr -f CSV ${folder}commune-names-cp1250.csv ${folder}OB/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT OB_MID, OB_UIME FROM 'SI.GURS.RPE.PUB.OB'"
iconv -f CP1250 -t UTF8 ${folder}commune-names-cp1250.csv -o ${folder}commune-names.csv
rm ${folder}commune-names-cp1250.csv

# Region names
ogr2ogr -f CSV ${folder}region-names-cp1250.csv ${folder}SR/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT SR_MID, SR_UIME FROM 'SI.GURS.RPE.PUB.SR'"
iconv -f CP1250 -t UTF8 ${folder}region-names-cp1250.csv -o ${folder}region-names.csv
rm ${folder}region-names-cp1250.csv

# Post codes
ogr2ogr -f CSV ${folder}post-codes.csv ${folder}PT/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT PT_MID, PT_ID FROM 'SI.GURS.RPE.PUB.PT'"

# spatial unit
ogr2ogr -f CSV ${folder}spatial-unit-region-mapping.csv ${folder}PO/ -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT PO_MID, SR_MID FROM 'SI.GURS.RPE.PUB.PO'"

ls -la ${folder}*.csv
wc -l ${folder}*.csv
head ${folder}*.csv


echo "  done."
echo -n "END:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"

#cd ..
