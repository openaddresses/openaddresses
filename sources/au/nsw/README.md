# statewide
## street/city regexp

Using PSMA Admin Boundaries data obtained with https://github.com/andrewharvey/psma-admin-bdys-data we are able to list all suburb/localities in NSW with:

    ogr2ogr -f CSV -select NAME -where "STATE_PID = '1'" /vsistdout/ Suburbs\ -\ Localities\ FEBRUARY\ 2018.shp | tail -n +2 | sort | uniq | sed ':a;N;$!ba;s/\n/|/g'

The output of that is used in the regexp for splitting street names and suburb/localities.

_Administrative Boundaries ©PSMA Australia Limited licensed by the Commonwealth of Australia under [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)._

## cached source

Install https://github.com/openaddresses/pyesridump and https://github.com/mapbox/geojson-merge, then run:

    mkdir -p NSW_Property
    for i in `seq 1 4`; do
        esri2geojson --timeout 360 -v http://maps.six.nsw.gov.au/arcgis/rest/services/public/NSW_Property/MapServer/$i NSW_Property/$i.geojson
    done
    geojson-merge --stream NSW_Property/*.geojson > NSW_Property.geojson
    zip NSW_Property.zip NSW_Property.geojson

### esri2geojson tips

 - The `esri2geojson` process will likely timeout at some point. You'll need to keep track of the offset and update this to resume where things were cut off, and then join all the outputs back together.
 - Assuming it does timeout, the `RID` field appears incremental, if you progressively change the `1=1` where clause to `RID>x` where `x` is some number then the queries will get progressively quicker and less likely to timeout.
 - Assuming it does timeout, after the first run if you hardcode the feature count, you'll shave 2-3 minutes off each subsequent run.
