# -*- coding: utf-8 -*-

import __future__
import csv, sys, json, copy, datetime, time, os

def readDictionary(path, filename):
    dict = {}
    with open(os.path.join(path, filename)) as f:
        reader = csv.reader(f, delimiter=';')
        next(reader) # skip header
        for row in reader:
            dict[row[0]] = row[1].strip()
            #print(streets[row[1]])

    print("Read %6d dictionary entries from %s" % (len(dict), filename))
    return dict

def main(path):
    # get timestamp from shapefiles
    timestamp = "" #datetime.datetime.now().strftime('%Y%m%d')
    with open(os.path.join(path, 'timestamp.txt'), 'r') as tsfile:
        timestamp = tsfile.read().replace('\n', '')

    # read dictionaries into memory as this is much faster to use then
    # (4 seconds vs 22 hours when processing by joining shapefiles using ogr2ogr on the same machine)

    # ==> street-names.csv <==
    # UL_MID;UL_UIME
    # 16183954;Župančičeva ulica
    # 16172839;Brezovce
    # 16183911;Liparjeva ulica
    streets = readDictionary(path, "street-names.csv")

    # ==> city-names.csv <==
    # NA_MID;NA_UIME
    # 10130000;Rovišče pri Studencu
    # 10084300;Podbreg
    # 10085900;Brdce
    cities = readDictionary(path, "city-names.csv")

    # ==> commune-names.csv <==
    # OB_MID;OB_UIME
    # 11027962;Novo mesto
    # 11027113;Mislinja
    # 11026982;Krško
    communes = readDictionary(path, "commune-names.csv")

    # ==> post-codes.csv <==
    # PT_MID;PT_ID
    # 21428698;8321
    # 21431125;8222
    # 21431656;5297
    postcodes = readDictionary(path, "post-codes.csv")

    # ==> region-names.csv <==
    # SR_MID;SR_UIME
    # 21428205;Jugovzhodna Slovenija
    # 21428132;Pomurska
    # 21428248;Goriška
    regions = readDictionary(path, "region-names.csv")

    # ==> spatial-unit-region-mapping.csv <==
    # PO_MID;SR_MID
    # 10347912;21428248
    # 10348471;21428248
    # 10348463;21428248
    spatregionmap = readDictionary(path, "spatial-unit-region-mapping.csv")

    # Main loop: transform
    # ==> addresses-noname.csv <==
    # X;Y;number;UL_MID;NA_MID;OB_MID;PO_MID;PT_MID;HS_MID
    # 13.917641089428125;45.926208653275097;64;16267520;10084270;11026516;10350212;21428337;11070205
    # 13.917586202711593;45.926379094149475;65;16267520;10084270;11026516;10350212;21428337;11070213
    # 13.917428708459077;45.926521570535712;67;16267520;10084270;11026516;10350212;21428337;11070230

    # to:
    # ==> si-addresses-YYYYMMDD.csv <==
    # lon;lat;number;street;city;commune;region;postcode;id
    # 13.917641089428125;45.926208653275097;64;Otlica;Otlica;Ajdovščina;Goriška;5270;11070205
    # 13.917586202711593;45.926379094149475;65;Otlica;Otlica;Ajdovščina;Goriška;5270;11070213
    # 13.917428708459077;45.926521570535712;67;Otlica;Otlica;Ajdovščina;Goriška;5270;11070230

    writer = csv.writer(open(os.path.join(path, 'si-addresses-{}.csv'.format(timestamp)), 'w'), delimiter=";")
    headers = ['lon', 'lat', 'number', 'street', 'city', 'commune', 'region', 'postcode', 'id']
    writer.writerow(headers)

    with open(os.path.join(path, "addresses-noname.csv")) as f:
        reader = csv.reader(f, delimiter=';')
        next(reader) # skip header

        for rowIn in reader:
            rowOut = rowIn

            # map IDs to values
            rowOut[3] = streets.get(rowIn[3], cities.get(rowIn[4], '??'))
            rowOut[4] = cities.get(rowIn[4], '??')
            rowOut[5] = communes.get(rowIn[5], '??')
            rowOut[6] = regions.get(spatregionmap.get(rowIn[6], '??'), '??')
            rowOut[7] = postcodes.get(rowIn[7], '??')

            writer.writerow(rowOut)


if __name__ == '__main__':
    main(path=sys.argv[1])
