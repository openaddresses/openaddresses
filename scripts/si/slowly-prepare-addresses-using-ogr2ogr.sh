#!/bin/bash

echo WARNING, this is OBSOLETE
echo It is a first, extremely slow approach (22hours vs. a minute using makeCSVs.sh and addNames.py)
echo just run make instead

inputFolder="${1}"
outputFolder="Addresses" #_${isoDate}_EPSG4326"

echo -n "START:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"
echo Making addresses with data ${splitId} from ${inputFolder} to folder ${outputFolder}:

cd ${inputFolder}

echo $PWD
# http://gis.stackexchange.com/questions/85028/dissolve-aggregate-polygons-with-ogr2ogr-or-gpc
ogr2ogr  -t_srs "EPSG:4326" -f CSV ${outputFolder}.csv HS/ -lco GEOMETRY=AS_XY -lco WRITE_BOM=YES -lco SEPARATOR=SEMICOLON -dialect sqlite \
 -sql "SELECT hs.geometry,
		hs.LABELA as number,
		CASE WHEN UL_ID <> 0 THEN UL.UL_UIME ELSE NA.NA_UIME END as street,
		NA.NA_UIME as city,
		OB.OB_UIME as commune,
		PT.PT_ID as postcode
	FROM 'SI.GURS.RPE.PUB.HS' AS hs
  		LEFT JOIN UL.'SI.GURS.RPE.PUB.UL' as UL ON hs.UL_MID = UL.UL_MID
  		LEFT JOIN NA.'SI.GURS.RPE.PUB.NA' as NA ON hs.NA_MID = NA.NA_MID
  		LEFT JOIN OB.'SI.GURS.RPE.PUB.OB' as OB ON hs.OB_MID = OB.OB_MID
  		LEFT JOIN PT.'SI.GURS.RPE.PUB.PT' as PT ON hs.PT_MID = PT.PT_MID
	" \
 -nln ${outputFolder}
echo "  done."

echo -n "END:	"
date -u +"%Y-%m-%dT%H:%M:%SZ"

cd ..
