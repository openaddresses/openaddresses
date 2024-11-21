Brazil 2022 census data
=======================

[IBGE](http://www.ibge.gov.br/), Brazil's statistics agency, published a complete list of addresses visited by the Census 2022 staff. For the first
time, this list included not only the complete address information but also the geolocation coordinates as captured by GPS of the census taker tablet.


This script downloads the original files from the IBGE website, combines it with the files in the data folder to resolve municipality, district and
subdistrict codes, and outputs a CSV file for each state in the output subfolder.

Usage:

    pip install requests
    python process_cnefe_2022.py

Requirements: Python 3 with requests package
