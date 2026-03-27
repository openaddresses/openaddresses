# Spain CartoCiudad Combine Script

This script combines all current CartoCiudad Spain packages into a single
zipped CSV containing only the address points layer (`portalpk_publi`).

## Requirements
- GDAL (`ogr2ogr`, `ogrinfo`)
- unzip

## Usage
```
./combine.sh /path/to/Spain [/path/to/output.csv.zip]
```

Example:
```
./combine.sh /Users/jeffunderwood/Downloads/Spain ./es_addresses.csv.zip
```
