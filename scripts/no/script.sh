#!/bin/bash

# used to do rm !(...)
shopt -s extglob

# creates directory SOStoCSV to unzip
mkdir SOStoCSV
unzip $1 -d SOStoCSV

# unzips all files into SOStoCSV
cd SOStoCSV
for i in *.zip; do
    unzip $i
done

# removes all files but Adresser.SOS
rm !(*Adresser.SOS)

for i in *.*; do
    temp=${i%.*}".csv"
    ogr2ogr -f csv -lco GEOMETRY=AS_XY -t_srs EPSG:4326 $temp $i
done

# removes all but csv files
rm -rf !(*.csv)

# move CSV to subdirectory, build CSV, minding that column order is not consistent
mkdir csv
mv *.csv ./csv
python make_out.py

# ignore the cadastral records -- we don't have street names for them
grep ",Gateadresse," no.csv > no-gateadresse.csv

# compress the result
zip no.zip no-gateadresse.csv
