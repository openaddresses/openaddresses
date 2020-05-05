# statewide
## street/city regexp

Using PSMA Admin Boundaries data obtained with https://github.com/andrewharvey/psma-admin-bdys-data we are able to list all suburb/localities in NSW with:

    ogr2ogr -f CSV -select NAME -where "STATE_PID = '1'" /vsistdout/ Suburbs\ -\ Localities\ NOVEMBER\ 2019.shp | tail -n +2 | sort | uniq | sed ':a;N;$!ba;s/\n/|/g'

The output of that is used in the regexp for splitting street names and suburb/localities.

_Administrative Boundaries ©PSMA Australia Limited licensed by the Commonwealth of Australia under [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)._

## cached source

Install https://github.com/openaddresses/pyesridump and https://github.com/mbostock/ndjson-cli, then run:

    mkdir -p NSW_Property
    for i in `seq 1 4`; do
        esri2geojson --timeout 360 -v --jsonlines --paginate-oid http://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Property/MapServer/$i NSW_Property/$i.geojson
    done
    cat NSW_Property/*.geojson | ndjson-reduce 'p.features.push(d), p' '{type: "FeatureCollection", features: []}' > NSW_Property.geojson
    rm -rf NSW_Property
    zip NSW_Property.zip NSW_Property.geojson
