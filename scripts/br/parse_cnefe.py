#!/usr/bin/env python3

import os
import glob
import zipfile
import fiona
import csv
import sys
from shapely.geometry import mapping, shape

FACES_SOURCE = '/downloads/faces'
ADDRESSES_SOURCE = '/downloads/addresses'
SHP_PATH = '/tmp/shp'
ADDRESSES_PATH = '/tmp/addresses'
RESULTS_PATH = '/results'

# Address files schema
txt_schema = [
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
csv_headers = [a for (a, b, c) in txt_schema]
csv_headers.extend(['subdistrict', 'district', 'municipality', 'state'])

# Load faces from shapefile
def load_faces(filename):
    coords = {}

    with fiona.open(filename) as shp:
        for r in shp:
            if r['geometry'] and r['properties']['CD_FACE']:
                cd_geo = r['properties']['CD_SETOR'] + \
                    r['properties']['CD_QUADRA'] + \
                    r['properties']['CD_FACE']
                try:
                    c = shape(r['geometry']).interpolate(0.5, normalized=True)
                    coords[cd_geo] = c
                except Exception as err:
                    print('Invalid geometry: ' + cd_geo, err, file=sys.stderr)

    return coords

# For a given shapefile and its id, parse addresses files
def parse_area(facesid, faces_shp, address_zips):
    faces = load_faces(faces_shp);

    # Expand addresses files
    for address_zip in address_zips[0:1]:
        with zipfile.ZipFile(address_zip, 'r') as zip_ref:
            zip_ref.extractall(ADDRESSES_PATH)

    for address_txt in glob.glob(ADDRESSES_PATH + '/*.TXT'):        
        parse_txt(faces, address_txt)

    # Clean temporary directory
    files = glob.glob(ADDRESSES_PATH + '/*')
    for f in files:
        os.remove(f)        

def parse_txt(faces, txt_file):
    count=0

    print('Parsing file: ' + txt_file)
    with open(txt_file, 'r', errors='replace') as lines:
        for line in lines:
            parse_line(faces, line)
            count += 1    
    
    print('Addresses found: ' + str(count))

def parse_line(faces, line):
    a = {}
    for (field, start, length) in txt_schema:
        a[field] = line[start-1:start-1+length].strip()

    # Common fixes
    a['census sector'] = a['census sector'].replace(' ', '0')
    a['postal code'] = a['postal code'].zfill(8)
    if a['number'] == '0':
        a['number'] = ''

    # Get face id
    cd_geo = a['census sector'] + a['block'] + a['face']

    # Get lng/lat, if available
    if a['lon']:
        try:
            a['lon'] = dms_to_decimal(a['lon'])
            a['lat'] = dms_to_decimal(a['lat'])
        except Exception as err:
            print('Warning:', err, file=sys.stderr)
            a['lon'] = ''
            a['lat'] = ''
    # Get lng/lat from faces
    elif cd_geo in faces:
        a['lon'] = str(faces[cd_geo].x)
        a['lat'] = str(faces[cd_geo].y)
    
    # Write record
    csv_writer.writerow(a)

# Helper function to convert DMS coordinates to decimal 
def dms_to_decimal(c):
    [d, m, s, q] = c.split()
    return (float(d) + float(m)/60 + float(s)/3600) * (-1 if q in ['O', 'S'] else 1)

# Entry point
global csv_writer
states_zip = glob.glob(
    FACES_SOURCE + '/**/*_faces_de_logradouros_2019.zip', recursive=True)
for state_zip in states_zip[24:25]:
    state_id=os.path.basename(state_zip)[0:2]

    # Clear tmp directory
    tmp_files=glob.glob('/tmp/**/*', recursive=True)
    for tmp_file in tmp_files:
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)


    print('Parsing state: ' + state_id)

    # Create CSV write stream
    with open(RESULTS_PATH + '/' + state_id + '.csv', 'w', newline='') as csvfile:
        csv_writer = csv.DictWriter(csvfile, csv_headers, extrasaction='ignore')
        csv_writer.writeheader()

        # Expand state shapefiles
        with zipfile.ZipFile(state_zip, 'r') as zip_ref:
            zip_ref.extractall(SHP_PATH)

        # Parse state shapefiles
        state_faces_shp = glob.glob(SHP_PATH + '/*_faces_de_logradouros_2019.shp')
        for faces_shp in state_faces_shp:
            faces_id = os.path.basename(faces_shp)[0:7]

            # Get addresses in shapefile area
            address_zips = glob.glob(
                ADDRESSES_SOURCE + '/**/' + faces_id + '*.zip', recursive=True)

            # Parse address file
            parse_area(faces_id, faces_shp, address_zips);

        # Clean temporary directory
        files = glob.glob(SHP_PATH + '/*')
        for f in files:
            os.remove(f)
