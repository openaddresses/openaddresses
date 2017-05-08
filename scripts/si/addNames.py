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
    # X;Y;number;UL_MID;NA_MID;OB_MID;PO_MID;PT_MID
    # 13.917661399610203;45.92620750719454;64;16267520;10084270;11026516;10350212;21428337
    # 13.917606514772237;45.926377945666744;65;16267520;10084270;11026516;10350212;21428337
    # 13.917449024108413;45.926520420054231;67;16267520;10084270;11026516;10350212;21428337

    # to:
    # ==> si-addresses-YYYYMMDD.csv <==
    # lon;lat;number;street;city;commune;region;postcode
    # 13.917661399610203;45.92620750719454;64;Otlica;Otlica;Ajdovščina;Goriška;5270
    # 13.917606514772237;45.926377945666744;65;Otlica;Otlica;Ajdovščina;Goriška;5270
    # 13.917449024108413;45.926520420054231;67;Otlica;Otlica;Ajdovščina;Goriška;5270

    writer = csv.writer(open(os.path.join(path, 'si-addresses-{}.csv'.format(timestamp)), 'w'), delimiter=";")
    headers = ['lon', 'lat', 'number', 'street', 'city', 'commune', 'region', 'postcode']
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

    # Adjust json template with new timestamps
#    template = {}
#    with open('at_source.json', 'r') as f:
#        template = json.load(f)
#    for srs in writers:
#        source = copy.deepcopy(template)
#        source['data'] = 'http://data.openaddresses.io/cache/at-{}.zip'.format(timestamp)
#        source['conform']['srs'] = 'EPSG:{}'.format(srs)
#        source['conform']['file'] = 'at-{}-{}.csv'.format(srs, timestamp)
#        source['attribution'] = '© Austrian address register, date data from {}'.format(datetime.datetime.now().isoformat().split('T')[0])
#        with open('at-{}.json'.format(srs), 'w') as f:
#            json.dump(source, f, indent=4)

#    print(timestamp)

if __name__ == '__main__':
    main(path=sys.argv[1])
