# BAG Light (GPKG) processing

Use `bag-light.sh` to download the BAG Light GeoPackage, extract the
`verblijfsobject` layer, convert it to CSV with X/Y columns, and zip the result:

```bash
./bag-light.sh
```

By default, outputs land in `scripts/nl/tmp-bag-light/` and the zipped CSV is
`verblijfsobject.csv.zip`. You can override the output directory with
`WORK_DIR=/path/to/dir ./bag-light.sh`.
