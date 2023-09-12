Brazil 2010 census data
=======================

[IBGE](http://www.ibge.gov.br/), Brazil's statistics agency, publishes a non-geocoded nationwide address list (CNEFE, _Cadastro Nacional de Endereços para Fins Estatísticos_) as well as a separate set of shapefiles from which an address can be located up to city block and sidewalk segment within the block.

This script combines the two databases and generates a csv output. Each address is positioned at the midpoint of the corresponding sidewalk segment.

Usage:

    make fetch
    make unpack
    make by_state

Requirements: Python 3 with Fiona and Shapely, and csvkit
