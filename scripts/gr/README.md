# Greece Countrywide Address Data

Greece publishes national street-name/number points via the Hellenic Cadastre,
but that dataset carries no city/municipality field — just a street name, a
declared number, and a coordinate. This pipeline joins those points against
the national municipality boundaries to attach a city name, and packages the
result as a single zipped CSV for OpenAddresses to conform.

## Sources

- **Declared streets** (2.29M points, `ADDRESS` + `NUM` fields, EGSA87/EPSG:2100):
  Hellenic Cadastre, via [data.gov.gr](https://data.gov.gr/dataset/16068541-970c-4d1a-8047-b95fd4d261ba/resource/946e2a6a-8ab8-4c62-89e3-e14ecd9868a1/download/ogp_hc_regstreets_egsa87.zip).
  Subject to the Hellenic Cadastre's [terms of use](https://www.ktimatologio.gr/oroi-xrisis)
  (embedded in the shapefile's own FGDC metadata) and licensed CC BY 4.0 per its
  data.gov.gr / data.europa.eu catalog record.
- **Municipality boundaries** ("Kallikratis" administrative divisions, 326
  polygons, same EPSG:2100 grid): Ministry of Environment & Energy (YPEN), served
  live from their GeoServer at
  [wfdservices.ypeka.gr](https://wfdservices.ypeka.gr/geoserver/WFD_geodata_50K/wfs?service=WFS&version=2.0.0&request=GetFeature&typeNames=WFD_geodata_50K%3Akallikratikoi_dimoi&outputFormat=application%2Fjson),
  sourced from geodata.gov.gr. CC BY 4.0.

No open national postal-code dataset exists for Greece (checked GeoNames,
DataHub, and the Greek/EU open-data catalogs — none have countrywide coverage),
so `postcode` is intentionally left out.

## Running

```
pip install -r requirements.txt
make combine
```

This downloads both sources into `data/` (gitignored) and writes
`out/gr_countrywide_addresses.csv.zip` — a zipped CSV with columns
`STREET, NUMBER, CITY, MUN_CODE, LON, LAT`.

To refresh later (e.g. after the Cadastre or Ministry update their data), just
delete `data/` and re-run `make combine`.

## Known data-quality issue

A subset of `NUMBER` values in the source are anomalously long numeric strings
(e.g. `0630278511`) rather than a normal house number — likely a different
identifier (possibly a parcel/KAEK code) that leaked into the field during the
original property-owner declaration process. Worth profiling and filtering
before treating this as clean address data.

## Rehosting

The join produces a ~300MB CSV (~2.29M rows), zipped down considerably. That
zip needs to be rehosted somewhere stable and public before
`sources/gr/countrywide.json` can point at it — update the `data` URL there and
clear the `skip` flag once that's done.
