#!/usr/bin/env bash

curl -L "https://download.geofabrik.de/europe/united-kingdom/england/isle-of-wight-latest.osm.pbf" > data.osm.pbf

osmconvert data.osm.pbf --all-to-nodes --out-o5m -o=data.o5m

osmfilter data.o5m --keep="addr:*=*" --keep-tags="all addr:*=*" -o=data.addr.osm

osmconvert data.addr.osm --csv="@lon @lat addr:flats addr:unit addr:housenumber addr:housename addr:substreet addr:street addr:parentstreet addr:place addr:hamlet addr:suburb addr:city addr:postcode addr:county addr:country"  -o=data.csv --csv-headline
