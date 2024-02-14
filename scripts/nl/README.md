The other files (nl-data.js, package.json, and run.sh) in this directory appear to be deprecated since the data is pulled from an ArcGIS server.

# Country-wide Netherlands

The sheer number of address points and buildings in this source (~9.7m and 11m, respectively) can cause request timeouts during machine processing, so these instructions are for periodically caching datasets by scraping the entire data with [pyesridump](https://github.com/openaddresses/pyesridump) and trimming for required properties.

Using [pyesridump](https://github.com/openaddresses/pyesridump), run:

```bash
esri2geojson https://basisregistraties.arcgisonline.nl/arcgis/rest/services/BAG/BAGv3/MapServer/0 netherlands_addresses.geojson.1
```

This source is ~9.7m records, so if it times out, pick back up where it left off by finding the last object returned:

```bash
tail -1 netherlands_addresses.geojson | jq '.properties.objectid'
```

Then run `esri2geojson` again to pick back up where it left off:

```bash
esri2geojson -p "WHERE=objectid > <# from above>" https://basisregistraties.arcgisonline.nl/arcgis/rest/services/BAG/BAGv3/MapServer/0 netherlands_addresses.geojson.2
```

If multiple attempts are needed to download all the data, then take all lines *except the first* (which is the GeoJSON header `{"type":"FeatureCollection","features":[`) for each file and remove trailing commas and unneeded properties with:

```bash
tail +2 netherlands_addresses.geojson.1 | sed 's/,$//' | jq -c -f filter-properties.jq > netherlands_addresses.geojson.trimmed.1
```

Combine the `netherlands_addresses.geojson.#` files into one with a `{"type":"FeatureCollection","features":[` prefix and `]}` suffix and commas appended.  The result file is a complete GeoJSON `FeatureCollection` object.

Next, zip with:

```bash
zip nl-countrywide.addresses.geojson.zip netherlands_addresses.geojson.final
```

Finally, contact someone on the OpenAddreses admin team to upload this file to s3.
