Brazil 2010 census data
=======================

[Brazil's statistics agency](http://www.ibge.gov.br/) publishes a non-geocoded nationwide address list (CNEFE, _Cadastro Nacional de Endereços para Fins Estatísticos_) as well as a separate set of shapefiles from which an address can be located up to city block and sidewalk segment within the block.

This script combines the two databases and generates a csv output. Each address is positioned at the midpoint of the corresponding sidewalk segment. Note that unit information is ignored and a single entry is generated for each street address.

Usage:

    make fetch
    make unpack
    make by_state
    
Requirements: Python 3 with Fiona and Shapely.
    
