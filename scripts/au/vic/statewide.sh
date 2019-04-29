#!/bin/sh

# Given a DELWP SpatialDatamart download URL for VICMAP ADDRESS,
#  - download it
#  - combines address.shp and address_1.shp (which are split to avoid a 2GB DBF
#    file limit, however since OA supports >2GB DBF files, they are combined)

url="$1"

if [ -z "$url" ] ; then
    echo 'Usage: ./statewide.sh URL_TO_ZIP'
    exit
fi

wget -O VICMAP_ADDRESS.zip "$url"
unzip -d VICMAP_ADDRESS VICMAP_ADDRESS.zip
cd VICMAP_ADDRESS
ogr2ogr -update -append ll_gda94/sde_shape/whole/VIC/VMADD/layer/address.shp ll_gda94/sde_shape/whole/VIC/VMADD/layer/address_1.shp
rm ll_gda94/sde_shape/whole/VIC/VMADD/layer/address_1*
rm ../VICMAP_ADDRESS.zip
zip -r ../VICMAP_ADDRESS.zip *
cd ..
rm -rf VICMAP_ADDRESS
