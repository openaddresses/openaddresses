#!/bin/sh

mkdir -p /tmp/work
SOURCE=/tmp/work/brisbane-source.csv
CSV=/tmp/work/brisbane.csv
OUTPUT=/tmp/work/brisbane.csv.zip
wget --output-document=$SOURCE "https://data.brisbane.qld.gov.au/api/explore/v2.1/catalog/datasets/property-address-locations/exports/csv?lang=en&use_labels=true&delimiter=%2C"

cat $SOURCE | csvgrep -c 'EASTING,NORTHING' -r '.+' > $CSV

mlr -I --csv put 'if (contains($EASTING, "|")) { $X = splita($EASTING, "|")[1] } else { $X = $EASTING }; if (contains($NORTHING, "|")) { $Y = splita($NORTHING, "|")[1] } else { $Y = $NORTHING }' $CSV

wc -l $CSV

zip --junk-paths $OUTPUT $CSV

echo $OUTPUT
