# au/tas LIST

## Install
If you already have a version of Chrome or Chromium which supports headless then install with:

    PUPPETEER_SKIP_CHROMIUM_DOWNLOAD=true yarn install

Otherwise a regular install will download a Puppeteer local Chrome to use:

    yarn install

## Prepare

Download the latest [ASGS LGA definitions](http://www.abs.gov.au/AUSSTATS/abs@.nsf/DetailsPage/1270.0.55.003July%202017?OpenDocument) and prepare this file with:

    wget -O '1270055003_lga_2017_tas_csv.zip' 'http://www.abs.gov.au/AUSSTATS/SUBSCRIBER.NSF/log?openagent&1270055003_lga_2017_tas_csv.zip&1270.0.55.003&Data%20Cubes&6A2078BEB18198A5CA25816B00135AD3&0&July%202017&31.07.2017&Latest'
    unzip -j 1270055003_lga_2017_tas_csv.zip
    rm 1270055003_lga_2017_tas_csv.zip
    csvcut -c 'LGA_CODE_2017,LGA_NAME_2017' LGA_2017_TAS.csv | tail -n+2 | sort | uniq | sed 's/\s(Tas\.)$//' | sed 's/\s([A-Z])//' | tr '\'/ ' '_' | grep -vE '(No_usual_address)|(Migratory_-_Offshore_-_Shipping)' > ASGS_LGA_2017_TAS.csv

## Run

`list.js` has a preset Chromium path of `/usr/bin/chromium`, you may need to change this to point to your Chrome/Chromium or simply remove the option to use the Puppeteer local Chrome.

    ./list.js
