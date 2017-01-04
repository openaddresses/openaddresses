#!/usr/bin/env python3

import csv, argparse, sys, locale, re
import fiona
from shapely.geometry import mapping, shape

parser = argparse.ArgumentParser(description="Convert CNEFE data to CSV format")
parser.add_argument('--no-subaddresses', action='store_true', help="Strip unit information")
parser.add_argument('r', help="CNEFE region id")
args = parser.parse_args()

fieldnames = [
    "lon",
    "lat",
    "census_sector",
    "block",
    "face",
    "urban_or_rural",
    "street_type",
    "street_title",
    "street_name",
    "number",
    "number_suffix",
    "suburb",
    "postcode",
    "subdistrict",
    "district",
    "municipality",
    "state",
]

if not args.no_subaddresses:
    fieldnames.extend([
        "unit_k1",
        "unit_v1",
        "unit_k2",
        "unit_v2",
        "unit_k3",
        "unit_v3",
        "unit_k4",
        "unit_v4",
        "unit_k5",
        "unit_v5",
        "unit_k6",
        "unit_v6",
        "addr_type",
        "note",
        "unique_or_multiple",
        "collective_dwelling",
    ])

def shrink(s):
    return ' '.join(s.split())

def dms_to_decimal(c):
    [d,m,s,q] = c.split()
    return (float(d) + float(m)/60 + float(s)/3600) * (-1 if q in ["O", "S"] else 1)

def do_file(r):

    count = r.copy()
    count['total'] = 0
    count['gps'] = 0
    count['on face'] = 0
    count['face missing'] = 0
    count['write failed'] = 0

    coords = {} # a dict with coordinates representing each block face

    try:
        with fiona.open("data/" + r["id"] + '_face.shp') as source:
            for x in source:
                c = shape(x['geometry']).interpolate(0.5, normalized=True)
                coords[x['properties']['CD_GEO']] = c
    except Exception as err:
        print("Error:", r["id"], err, file=log)

    with open("data/" + r["id"] + ".TXT", 'r', errors='replace') as f:
    
        for l in f:
        
            a = r.copy() # initialize with subdistrict data

            count['total'] += 1

            a["census_sector"] = l[0:15]
            a["urban_or_rural"] = l[15]
            a["street_type"] = shrink(l[16:36])
            a["street_title"] = shrink(l[36:66])
            a["street_name"] = shrink(l[66:126])
            a["number"] = shrink(l[126:134])
            a["number_suffix"] = shrink(l[134:141])
            a["unit_k1"] = shrink(l[141:161])
            a["unit_v1"] = shrink(l[161:171])
            a["unit_k2"] = shrink(l[171:191])
            a["unit_v2"] = shrink(l[191:201])
            a["unit_k3"] = shrink(l[201:221])
            a["unit_v3"] = shrink(l[221:231])
            a["unit_k4"] = shrink(l[231:251])
            a["unit_v4"] = shrink(l[251:261])
            a["unit_k5"] = shrink(l[261:281])
            a["unit_v5"] = shrink(l[281:291])
            a["unit_k6"] = shrink(l[291:311])
            a["unit_v6"] = shrink(l[311:321])
            a["lat"] = l[321:336].strip()
            a["lon"] = l[336:351].strip()
            a["suburb"] = shrink(l[351:411])
            a["addr_type"] = l[471:473]
            a["note"] = shrink(l[473:513])
            a["unique_or_multiple"] = l[513].strip()
            a["collective_dwelling"] = shrink(l[514:544])
            a["block"] = l[544:547]
            a["face"] = l[547:550]
            a["postcode"] = l[550:558]

            #cleanups
            a['census_sector'] = a['census_sector'].replace(' ', '0')

            if a['number'] == '0':
                a['number'] = ''

            #find coordinates
            cd_geo = a["census_sector"] + a["block"] + a["face"]

            if a["lon"]:
                a["lon"] = dms_to_decimal(a["lon"])
                a["lat"] = dms_to_decimal(a["lat"])
                count['gps'] += 1
            elif cd_geo in coords:
                count['on face'] += 1
                a["lon"] = str(coords[cd_geo].x)
                a["lat"] = str(coords[cd_geo].y)
            else:
                count['face missing'] += 1

            try:
                out.writerow(a)
            except:
                count['write failed'] += 1

    print(count, file=log)

manifest = csv.DictReader(open('manifest.csv'))

log = open(args.r + ".log", 'w')
out = csv.DictWriter(sys.stdout, fieldnames, extrasaction="ignore")
out.writeheader()

for s in manifest:
    if s["id"].startswith(args.r):
        try:
            do_file(s)
        except Exception as err:
            print("Error:", s["id"], err, file=log)

