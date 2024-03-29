import json
import math
import sys
import logging

from esridump.dumper import EsriDumper

logging.basicConfig(level=logging.DEBUG)

outfile_name = sys.argv[1] if len(sys.argv) > 1 else 'bogota.geojson'

d = EsriDumper('http://serviciosgis.catastrobogota.gov.co/arcgis/rest/services/Mapa_Referencia/Mapa_Referencia/MapServer/33')

outfile = open(outfile_name, 'w')

outfile.write('{"type":"FeatureCollection","features":[\n')

features = iter(d)

try:
    feature = next(features)

    while True:
        if not feature.get('geometry') or feature['geometry']['coordinates'][0] == 'NaN' or (type(feature['geometry']['coordinates'][0]) is float and math.isnan(feature['geometry']['coordinates'][0])):
            feature = next(features)
            continue
        props = feature['properties']
        interior = props['PDoCInteri']
        if interior and interior.strip():
            street = props['PDoTexto']
            if street and street.strip() and not street.strip()[0].isdigit():
                props['PDoCInteri'] = street
                props['PDoTexto'] = interior
        outfile.write(json.dumps(feature))
        feature = next(features)
        outfile.write(',\n')
except StopIteration:
    outfile.write('\n')

outfile.write(']}')
