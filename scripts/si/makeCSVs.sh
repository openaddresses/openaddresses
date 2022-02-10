#!/bin/bash
set -e
folder="${1}"

echo -n "START:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"
echo "Making CSVs from shapefiles within ${folder}:"
export SHAPE_ENCODING=CP1250
rm -f "${folder}"*.csv

stat -c '%y' "${folder}HS/HS.shp"  | cut -d' ' -f1 > "${folder}timestamp.txt"

# http://gis.stackexchange.com/questions/85028/dissolve-aggregate-polygons-with-ogr2ogr-or-gpc
ogr2ogr -t_srs "EPSG:4326" -s_srs "EPSG:3794" -f CSV "${folder}addresses-noname.csv" "${folder}HS/" -lco GEOMETRY=AS_XY -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT geometry,
		LABELA as number,
		UL_MID,
		NA_MID,
		OB_MID,
		PO_MID,
		PT_MID,
		HS_MID
	FROM 'HS'
	WHERE STATUS ='V'
	ORDER BY OB_MID, NA_MID, UL_MID, HS, HD, HS_MID" \
 -nln addresses-noname

# Street names
ogr2ogr -f CSV "${folder}street-names.csv" "${folder}UL/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT UL_MID, UL_UIME || CASE WHEN UL_DJ IS NULL THEN '' ELSE ' / ' || UL_DJ END AS UL_NAME FROM 'UL'"

# City names
ogr2ogr -f CSV "${folder}city-names.csv" "${folder}NA/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT NA_MID, NA_UIME || CASE WHEN NA_DJ IS NULL THEN '' ELSE ' / ' || NA_DJ END AS NA_NAME FROM 'NA'"

# Commune names
ogr2ogr -f CSV "${folder}commune-names.csv" "${folder}OB/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT OB_MID, OB_UIME FROM 'OB'"

# Region names
ogr2ogr -f CSV "${folder}region-names.csv" "${folder}SR/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT SR_MID, SR_UIME FROM 'SR'"

# Post codes
ogr2ogr -f CSV "${folder}post-codes.csv" "${folder}PT/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT PT_MID, PT_ID FROM 'PT'"

# spatial unit
ogr2ogr -f CSV "${folder}spatial-unit-region-mapping.csv" "${folder}PO/" -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT PO_MID, SR_MID FROM 'PO'"

file "${folder}"*.csv
ls -la "${folder}"*.csv
wc -l "${folder}"*.csv
head "${folder}"*.csv


echo "  done."
echo -n "END:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"
