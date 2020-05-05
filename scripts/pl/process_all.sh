#!/bin/bash

DATA_SOURCE='https://opendata.geoportal.gov.pl/prg/adresy/PRG-punkty_adresowe.zip'

echo "Downloading sources..."
wget DATA_SOURCE

echo "Unzipping..."
unzip -O PRG-punkty_adresowe.zip

echo "Removing data prefixes..."
for file in *.xml
do
    new_file_name=`echo $file | cut -d '_' -f 9`
    mv $file $new_file_name
    python3 process_one.py
done

echo "Done"