# Openaddresses HK

## Run

```sh
uv run hk.py
```

Keep the downloaded source ZIP and extracted GeoJSON files:

```sh
uv run hk.py --keep-intermediate
```

## Schema Conversion

The source GeoJSON stores address data in nested objects such as
`Address -> PremisesAddress -> ChiPremisesAddress` and
`Address -> PremisesAddress -> EngPremisesAddress`.

The HK script flattens those nested properties into a single record:

- Chinese fields are normalized to `zh_*` keys, with the original `Chi` prefix removed.
- English fields are normalized to `en_*` keys, with the original `Eng` prefix removed.
- `StreetNumber` is derived from the building number fields:
  - if only `BuildingNoFrom` exists, `StreetNumber` uses that value
  - if both `BuildingNoFrom` and `BuildingNoTo` exist, `StreetNumber` is joined as `BuildingNoFrom-BuildingNoTo`
- Geometry coordinates are written to `Longitude` and `Latitude`.

Example output fields:

- `zh_District`
- `zh_StreetName`
- `en_District`
- `en_StreetName`
- `BuildingNoFrom`
- `BuildingNoTo`
- `StreetNumber`
- `Longitude`
- `Latitude`

## Archive behavior

`hk.py` looks for a source ZIP in `scripts/hk/`.

- If `ALS_GeoJSON.zip` or any `ALS_GeoJSON*.zip` file already exists there, the script uses it directly and does not attempt a download.
- If that file is missing, the script downloads the current archive from CSDI, caches it at `scripts/hk/ALS_GeoJSON.zip`, and then processes it.
- If the automatic CSDI download flow fails, the script prints the dataset page URL and asks you to download the ZIP manually and place it in `scripts/hk/` as either `ALS_GeoJSON.zip` or the original CSDI-style filename such as `ALS_GeoJSON_324.zip`.
- By default, the script deletes the source ZIP it used and the extracted `geojson_files/` directory after processing completes, even if the ZIP already existed before the run.
- Pass `--keep-intermediate` to skip that cleanup.
