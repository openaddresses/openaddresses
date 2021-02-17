# Brazil 2010 census data

[IBGE](http://www.ibge.gov.br/), Brazil's statistics agency, publishes a non-geocoded nationwide address list (CNEFE, _Cadastro Nacional de Endereços para Fins Estatísticos_) as well as a separate set of shapefiles from which an address can be located up to city block and sidewalk segment within the block.

This script combines the two databases and generates a csv output. Each address is positioned at the midpoint of the corresponding sidewalk segment.

## Parse to OpenAddresses format

Requirements:

- wget
- Docker

Download source data:

    ./download-sources.sh

This command will mirror files available at IBGE FTP in `/downloads/faces` and `/downloads/addresses` folders. This might take a long time, please check [this repo](https://github.com/vgeorge/cnefe) for alternative p2p download.

Build and run docker image:

    docker-compose up --build

Output files will be available in `/results` folder.
