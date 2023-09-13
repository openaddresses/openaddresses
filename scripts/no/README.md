# Norwegian Conversion Script


The Norwegian Address data is located at: http://data.kartverket.no/download/content/elveg-utm-33-hele-landet behind a registration wall. The archive consists of 400+ zip files using Norway-specific SOS format.

Requirements:
GDAL with support for the Norwegian SOSI format.
Instructions can be found here: http://trac.osgeo.org/gdal/wiki/SOSI

It takes a zip file as a command line argument, unzips everything and converts all Adresser.SOS into their respective CSV files.
```
$ bash script.sh {target zip file}
```
All the CSV files will be in a newly created folder named SOStoCSV.

The final CSV lives in https://data.openaddresses.io/cache/no.zip
