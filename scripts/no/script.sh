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