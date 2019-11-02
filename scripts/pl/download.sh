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
done

echo "Renaming xml to gml..."
for file in *.xml
do
    file_name=`echo $file | cut -d '.' -f 1`
    mv $file "$file_name.gml"
done

mkdir 

echo "Renaming wrongly encoded file names"
mv 'dolno#U015bl#U0105skie.gml' 'dolnośląskie.gml'
mv '#U0142#U00f3dzkie.gml' 'łódzkie.gml'
mv 'ma#U0142opolskie.gml' 'małopolskie.gml'
mv '#U015bl#U0105skie.gml' 'śląskie.gml'
mv '#U015bwi#U0119tokrzyskie.gml' 'świętokrzyskie.gml'
mv 'warmi#U0144sko-mazurskie.gml' 'warmińsko-mazurskie.gml'
echo "Done"
