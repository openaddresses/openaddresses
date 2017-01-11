#!/usr/bin/env python3

import csv, argparse, sys, locale, re
import fiona
from shapely.geometry import mapping, shape

parser = argparse.ArgumentParser(description='Convert CNEFE data to CSV format')
parser.add_argument('region', help='CNEFE region id')
args = parser.parse_args()

cnefe_schema = [
    # see data/Layout_Donwload.xls for details
    ('census sector', 1, 15),
    ('sector type', 16, 1),
    ('street type', 17, 20),
    ('street title', 37, 30),
    ('street name', 67, 60),
    ('number', 127, 8),
    ('number suffix', 135, 7),
    ('unit k1', 142, 20),
    ('unit v1', 162, 10),
    ('unit k2', 172, 20),
    ('unit v2', 192, 10),
    ('unit k3', 202, 20),
    ('unit v3', 222, 10),
    ('unit k4', 232, 20),
    ('unit v4', 252, 10),
    ('unit k5', 262, 20),
    ('unit v5', 282, 10),
    ('unit k6', 292, 20),
    ('unit v6', 312, 10),
    ('lat', 322, 15),
    ('lon', 337, 15),
    ('locality', 352, 60),
    ('address type', 472, 2),
    ('note', 474, 40),
    ('unique or multiple', 514, 1),
    ('collective dwelling', 515, 30),
    ('block', 545, 3),
    ('face', 548, 3),
    ('postal code', 551, 8)
]

def dms_to_decimal(c):
    [d,m,s,q] = c.split()
    return (float(d) + float(m)/60 + float(s)/3600) * (-1 if q in ['O', 'S'] else 1)

def parse_line(l, initial):
    a = initial.copy()
    for (field, start, length) in cnefe_schema:
        a[field] = l[start-1:start-1+length].strip()

    # cleanups
    a['census sector'] = a['census sector'].replace(' ', '0')
    a['postal code'] = a['postal code'].zfill(8)
    if a['number'] == '0':
        a['number'] = ''
        
    return a

def do_file(region):

    count = region.copy()
    for c in log_fields:
        count[c] = 0

    coords = {} # a dict of coordinates representing each block face

    try:
        with fiona.open('data/' + region['id'] + '_face.shp') as source:
            for x in source:
                if x['geometry']:
                    c = shape(x['geometry']).interpolate(0.5, normalized=True)
                    coords[x['properties']['CD_GEO']] = c
    except IOError as err:
        print('Warning:', err, file=sys.stderr)

    with open('data/' + region['id'] + '.TXT', 'r', errors='replace') as cnefe_file:
    
        for line in cnefe_file:
        
            count['total'] += 1

            a = parse_line(line,region)

            if a['number']:
                count['has number'] += 1
                
            #find coordinates
            cd_geo = a['census sector'] + a['block'] + a['face']

            if a['lon']:
                try:
                    a['lon'] = dms_to_decimal(a['lon'])
                    a['lat'] = dms_to_decimal(a['lat'])
                    count['gps'] += 1
                except Exception as err:
                    print('Warning:', err, file=sys.stderr)
                    a['lon'] = ''
                    a['lat'] = ''
            elif cd_geo in coords:
                count['has face'] += 1
                a['lon'] = str(coords[cd_geo].x)
                a['lat'] = str(coords[cd_geo].y)
            else:
                count['no coords'] += 1

            try:
                out.writerow(a)
            except Exception as err:
                print('Warning:', err, file=sys.stderr)

    for c in ['has number', 'has face', 'gps', 'no coords']:
        count[c] = '{:.1%}'.format(count[c]/count['total'])
                
    log.writerow(count)

manifest_fields = ['state', None, 'municipality', None, 'district',
                    None, 'subdistrict', 'id']
log_fields = ['total', 'has number', 'has face', 'gps', 'no coords']

manifest = csv.DictReader(open('data/manifest.csv'), fieldnames = manifest_fields)

if next(manifest) != {None: 'Subdistrito', 'state': 'UF', 'id': 'Arquivo', 'district': 'Nome Distrito', 'subdistrict': 'Nome Subdistrito', 'municipality': 'Nome Município'}:
    sys.exit("Error: Couldn't understand manifest file")

outfields = [a for (a,b,c) in cnefe_schema]    
outfields.extend(['subdistrict','district','municipality','state'])

log = csv.DictWriter(open(args.region + '.log', 'w'),
                     log_fields + ['id', 'municipality','state'],
                     extrasaction='ignore')
log.writeheader()

out = csv.DictWriter(sys.stdout, outfields, extrasaction='ignore')
out.writeheader()

for s in manifest:
    if s['id'].startswith(args.region):
        print('Info: processing ' + s['id'], file=sys.stderr)
        try:
            do_file(s)
        except IOError as err:
            print('Warning:', err, file=sys.stderr)
