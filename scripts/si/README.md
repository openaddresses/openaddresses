# Scripts for preparing countrywide addresses for Slovenia


### Steps:
1. Register as user at http://egp.gu.gov.si/egp, wait for the email with the password, login
2. Run GNU `make` in this folder (requires `wget`, gdal `ogr2ogr` and `python`)
3. When prompted enter your credentials (they can be saved for later reuse)
4. Wait a minute or two for processing to finish.

### To manually download the data you should:
1. Register as user at http://egp.gu.gov.si/egp, wait for the email with the password, login
2. Expand section "9. Register prostorskih enot"
3. Download the data "Prostorske enote" (spatial units) -> RPE_PE.ZIP and put it in this folder
4. Download the data "Ulice" (streets) -> RPE_PUL.ZIP and put it in this folder
5. Download the data "Hišne številke" (house numbers) -> RPE_PE.ZIP and put it in this folder
6. Adjust the scripts to use these ZIPs.

### Technical info:
Encoding in source shapefiles is Windows-1250 (`CP1250` in `iconv`), result is UTF8

Source shapefile structure is described in http://www.e-prostor.gov.si/fileadmin/struktura/RPE_struktura.pdf

### Dataset source
Data can be obtained from Geodetska  uprava  Republike  Slovenije - http://egp.gu.gov.si/egp/ under CreativeCommons attribution license - CC-BY 2.5 (http://creativecommons.org/licenses/by/2.5 ), attribution details: http://www.e-prostor.gov.si/fileadmin/struktura/preberi_me.pdf

### Dependancies
GeoCoordinateConverter for most accurate reprojection
https://github.com/mrihtar/GeoCoordinateConverter (included as git submodule)

For headless operation on machines without X11 libraris you will need to remove compilation of GUI, 
Do so in `GeoCoordinateConverter/Makefile.unix`:
diff:
```
-TGTS = gk-slo gk-shp xgk-slo
+TGTS = gk-slo gk-shp
```
