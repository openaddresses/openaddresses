#!/bin/sh

mkdir -p /tmp/work
ZIP=/tmp/work/brisbane_source.zip
CSV=/tmp/work/brisbane.csv
OUTPUT=/tmp/work/brisbane.csv.zip
wget -O - 'https://www.data.brisbane.qld.gov.au/data/api/3/action/package_show?id=property-address-data' | jq --raw-output '.result.resources[].url' | grep 'address' | wget --input-file=- --output-document=$ZIP

zcat $ZIP | csvgrep -c 'EASTING,NORTHING' -r '.+' > $CSV

mlr -I --csv put 'if (contains($EASTING, "|")) { $X = splita($EASTING, "|")[1] } else { $X = $EASTING }; if (contains($NORTHING, "|")) { $Y = splita($NORTHING, "|")[1] } else { $Y = $NORTHING }' $CSV

wc -l $CSV

zip --junk-paths $OUTPUT $CSV

echo $OUTPUT
