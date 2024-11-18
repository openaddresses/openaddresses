# au/qld/moreton_bay script

The source data includes a field for number and city, however the street only appears in a full address field, so we must strip out the number and city from the address field to reveal the street. OpenAddresses claims this is supported through use of a `chain` function with `remove_prefix` and `remove_postfix` functions however there were issues doing so in https://github.com/openaddresses/openaddresses/pull/6067.

Therefore this simple NodeJS script is used to perform the same function as a pre-processing stage.

```sh
wget -O 'moreton_bay.geojson` 'https://opendata.arcgis.com/api/v3/datasets/be1d48c1e8764baea256186b6eb28274_0/downloads/data?format=geojson&spatialRefId=4326'

./index.js

zip --junk-paths moreton_bay.geojson.zip moreton_bay.openaddresses.geojson
```
