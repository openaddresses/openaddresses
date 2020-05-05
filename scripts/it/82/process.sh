#!/bin/sh

# The original file comes from http://www.regione.sicilia.it/opendata/Numeri_Civici_CTN2000.zip

for f in *.geojson; do ogr2ogr -update -append merge.sqlite $f -f "SQLite" -dsco SPATIALITE=YES -nln "addresses"; done;
ogr2ogr -f geojson addresses.geojson merge.sqlite addresses
