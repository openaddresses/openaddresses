# Scripts for preparing countrywide addresses for Slovenia

## Steps:
1. Register as user at http://egp.gu.gov.si/egp, wait for the email with the password
2. Run GNU `make` in this folder (requires wget and python)
3. When prompted enter your credentials (they can be saved for later use)
4. Wait a minute or two for processing to finish.

## To manually download the data you should:
1. Register as user at http://egp.gu.gov.si/egp, wait for the email with the password
2. Expand section "9. Register prostorskih enot"
3. Download the data "Prostorske enote" (spatial units) -> RPE_PE.ZIP and put it in this folder
4. Download the data "Ulice" (streets) -> RPE_PUL.ZIP and put it in this folder
5. Download the data "Hišne številke" (house numbers) -> RPE_PE.ZIP and put it in this folder

## Technical info:
Encoding in shapefiles is Windows-1250 (`CP1250` in `iconv`), result is UTF8
