# BAG Light (GPKG) processing

Use `bag-light.sh` to download the BAG Light GeoPackage, extract the
`verblijfsobject` layer, convert it to CSV with X/Y columns, and zip the result.

Requirements:
- `ogr2ogr` (GDAL)
- `zip`
- `aria2c` (optional, for parallel download) or `curl`/`wget`

```bash
./bag-light.sh
```

By default, outputs land in `scripts/nl/tmp-bag-light/` and the zipped CSV is
`verblijfsobject.csv.zip`. You can override the output directory with
`WORK_DIR=/path/to/dir ./bag-light.sh`.

If `aria2c` is available, the script uses 16 parallel connections for a faster
download and resume support. It falls back to `curl` or `wget` otherwise.

Disk space: expect at least 12–16 GB free (downloaded GPKG + CSV + ZIP).
Runtime: depends on network and disk speed; plan for 30–120 minutes.
