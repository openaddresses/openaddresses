mkdir -p Saarland

# The amount of increments will need to increase if the dataset increases in count
for i in {1..134}; do
    offset=$(($i * 2500))
    curl='/usr/bin/curl'
    url="https://geoportal.saarland.de/spatial-objects/416/collections/GDI_ALKIS_Gebaeude:Hauskoordinaten/items?f=xml&limit=2500&offset=$offset"
    args="-o Saarland/$i.xml"
    $curl $url $args
done

ogrmerge -single -f csv -lco GEOMETRY=AS_XY -o Saarland.csv Saarland/*.xml
zip Saarland.zip Saarland.csv
