# Scripts for preparing countrywide addresses for Slovenia


### Steps:
1. Register as user at https://egp.gu.gov.si/egp/?lang=en, wait for the email with the password, login
2. Run GNU `make` in this folder (requires `wget`, gdal `ogr2ogr` and `python`)
3. When prompted enter your credentials (they can be saved for later reuse)
4. Wait a minute or two for processing to finish.

### To manually download the data you should:
1. Register as user at https://egp.gu.gov.si/egp/?lang=en, wait for the email with the password, login
2. Expand section "9. Register prostorskih enot" / "9. Register of Spatial Units"
3. Download the data "Prostorske enote" / "Spatial units" -> `RPE_PE.ZIP` and put it in this folder
4. Download the data "Ulice" / "Streets" -> `RPE_PUL.ZIP` and put it in this folder
5. Download the data "Hišne številke" / "House numbers" -> `RPE_PE.ZIP` and put it in this folder
6. Adjust the scripts to use these ZIPs.

### Technical info:
Encoding in source shapefiles is Windows-1250 (`CP1250`), result is UTF8

Source shapefile structure is described:
* Addresses in [RPE_struktura.pdf](https://www.e-prostor.gov.si/fileadmin/struktura/RPE_struktura.pdf) (only in Slovenian so far)
* Building footprints in [KS_format_15.pdf](https://www.e-prostor.gov.si/fileadmin/struktura/KS_format_15.pdf) (only in Slovenian so far)

### Dataset source
Data can be obtained from Geodetska  uprava  Republike  Slovenije - https://egp.gu.gov.si/egp/ under CreativeCommons attribution license - [CC-BY 4.0](https://creativecommons.org/licenses/by/4.0/), attribution details in  [General_terms.pdf](https://www.e-prostor.gov.si/fileadmin/struktura/ANG/General_terms.pdf) (or slovene [preberi_me.pdf](https://www.e-prostor.gov.si/fileadmin/struktura/preberi_me.pdf)).

### Dependancies
1. GNU Make, bash, wget... (normal linux stuff)
2. `ogr2ogr` (part of [gdal suite](https://gdal.org/))
3. Python 2
