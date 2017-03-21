#!/bin/bash
# Processing Kazakhstan data


# Dumping the data from ESRI servers
esri2geojson http://infopublic.pravstat.kz:8399/arcgis/rest/services/addr/MapServer/2 kz-countrywide.json
esri2geojson http://infopublic.pravstat.kz:8399/arcgis/rest/services/addr/MapServer/1 kz-countrywide-str.json
esri2geojson http://infopublic.pravstat.kz:8399/arcgis/rest/services/addr/MapServer/3 kz-countrywide-reg.json


# Putting it in an SQLite database for joining
ogr2ogr -f "SQLite" -nln "addr" kz.db kz-countrywide.json
ogr2ogr -f "SQLite" -append -nln "str" kz.db kz-countrywide-str.json
ogr2ogr -f "SQLite" -append -nln "reg" kz.db kz-countrywide-reg.json


# Getting the formatted data our
ogr2ogr -f "csv" -sql "select trim(addr.name) as number, trim(str.name) as street, trim(ro.name) as region, trim(rr.name) as district, x_point, y_point from addr left join str on id_street = str.id and addr.id_reg = str.id_reg left join reg ro on addr.id_city = ro.id left join reg rr on addr.id_reg = rr.id" kz.csv kz.db
