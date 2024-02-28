#!/usr/bin/env python3

import subprocess
import os
from pathlib import Path
import shutil
import glob
import zipfile
import fiona
import csv
import sys
from shapely.geometry import mapping, shape

FACES_2019_SOURCE = '/downloads/faces/2019'
FACES_2010_SOURCE = '/downloads/faces/2010'
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


def log_error(txt):
    with open(RESULTS_PATH + "/errors.txt", "a") as myfile:
        myfile.write(txt + '\n')

# Load dictionary of admin areas from 2010 csv file
def load_admin_areas():
    result = {
        'municipality': {},
        'district': {},
        'subdistrict': {}
    }
    with open('composicao_dos_arquivos_da_Base_de_Faces_de_Logradouros_do_CD2010.csv', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            result['municipality'][row['Município']] = {
                'municipality': row['Nome Município'],
                'state': row['UF']
            }

            result['district'][row['Município'] + row['Distrito']] = {
                'district': row['Nome Distrito'],
                'municipality': row['Nome Município'],
                'state': row['UF']
            }

            result['subdistrict'][row['Arquivo']] = {
                'subdistrict': row['Nome Subdistrito'],
                'district': row['Nome Distrito'],
                'municipality': row['Nome Município'],
                'state': row['UF']
            }

    return result

# Helper function to convert DMS coordinates to decimal
def dms_to_decimal(c):
    [d, m, s, q] = c.split()
    return (float(d) + float(m)/60 + float(s)/3600) * (-1 if q in ['O', 'S'] else 1)

# Get dictionary of faces from a state zipfile
def load_faces_midpoints(state_code, state_zip):
    midpoints = {}
    missing_shapefiles=set()

    # Expand zip
    with zipfile.ZipFile(state_zip, 'r') as zip_ref:
        zip_ref.extractall(SHP_PATH)

    # Get midpoints from 2019 shapefile and add to dictionary
    shapefiles_2019 = glob.glob(SHP_PATH + '/*_faces_de_logradouros_2019.shp')
    for faces_2019_shapefile in shapefiles_2019:
        print('Loading ' + faces_2019_shapefile + '...')
        try:
            with fiona.open(faces_2019_shapefile) as shp:
                for r in shp:
                    if r['geometry'] and r['properties']['CD_FACE']:
                        cd_geo = r['properties']['CD_SETOR'] + \
                            r['properties']['CD_QUADRA'] + \
                            r['properties']['CD_FACE']
                        try:
                            c = shape(r['geometry']).interpolate(
                                0.5, normalized=True)
                            midpoints[cd_geo] = [str(c.x), str(c.y)]
                        except Exception as err:
                            print('Invalid geometry: ' +
                                cd_geo, err, file=sys.stderr)
        except:
            missing_shapefiles.add(faces_2019_shapefile)


    # Get state id from first key
    state_id = next(iter(midpoints))[0:2]

    # Get midpoints from 2010 shapefile and add to dictionary
    zipfiles_2010 = glob.glob(
        FACES_2010_SOURCE + '/**/'+state_id + '*.zip', recursive=True)
    for faces_2010_zipfile in zipfiles_2010:
        with zipfile.ZipFile(faces_2010_zipfile, 'r') as zip_ref:
            zip_ref.extractall(SHP_PATH)


        # Get sector id
        file_basename = os.path.basename(faces_2010_zipfile)
        sector_id = os.path.splitext(file_basename)[0]

        # Get midpoints for sector file
        faces_2010_shapefile = SHP_PATH+'/' + sector_id + '_face.shp'
        print('Loading ' + faces_2010_shapefile + '...')

        try:
            with fiona.open(faces_2010_shapefile) as shp:
                for r in shp:
                    if r['geometry'] and r['properties']['CD_GEO']:
                        cd_geo = r['properties']['CD_GEO']
                        try:
                            c = shape(r['geometry']).interpolate(
                                0.5, normalized=True)
                            midpoints[cd_geo] = [str(c.x), str(c.y)]
                        except Exception as err:
                            print('Invalid geometry: ' +
                                cd_geo, err, file=sys.stderr)
        except:
            missing_shapefiles.add(faces_2010_shapefile)

    if (len(missing_shapefiles) > 0):
        with open(RESULTS_PATH + '/'+state_id+'-missing_shapefiles.csv', 'w') as missing_shapefiles_file:
            missing_shapefiles_file.writelines(
                "%s\n" % i for i in sorted(missing_shapefiles))

    return [state_id, midpoints]


def parse_addresses(state_id, midpoints, admin_areas):
    file_stats = {
        'total': 0,
        'has_own_coords': 0,
        'has_face_coords': 0,
        'missing_coords': 0,
        'missing_areas': 0
    }
    missing_faces = set()
    missing_areas = set()

    # Create CSV file
    with open(RESULTS_PATH + '/' + state_id + '.csv', 'w', newline='') as csvfile:
        # Write header
        csv_writer = csv.DictWriter(
            csvfile, csv_headers, extrasaction='ignore')
        csv_writer.writeheader()

        # Get zipfiles to this state
        address_zipfiles = glob.glob(ADDRESSES_SOURCE + '/**/'+state_id+'*.zip', recursive=True);

        for address_zipfile in address_zipfiles:

            # Clear tmp address path
            shutil.rmtree(ADDRESSES_PATH)

            # Expand zipfile with system unzip, zipfile module can't handle large files
            subprocess.run(["unzip", address_zipfile, "-d", ADDRESSES_PATH])

            # Parse textfile, assume zipfile has only one file
            # address_textfile = ADDRESSES_PATH + '/' + Path(address_zipfile).stem + '.txt'
            [address_textfile] = glob.glob(ADDRESSES_PATH + '/*')

            print('Parsing ' + address_textfile + '...')
            with open(address_textfile, 'r', errors='replace') as lines:

                # Parse lines
                for line in lines:
                    file_stats['total'] += 1
                    addr = {}
                    for (field, start, length) in txt_schema:
                        addr[field] = line[start-1:start-1+length].strip()

                    # Common fixes
                    addr['census sector'] = addr['census sector'].replace(' ', '0')
                    addr['postal code'] = addr['postal code'].zfill(8)
                    if addr['number'] == '0':
                        addr['number'] = ''

                    # Get face id
                    cd_geo = addr['census sector'] + addr['block'] + addr['face']

                    # Get lng/lat, if available
                    if addr['lon']:
                        try:
                            addr['lon'] = dms_to_decimal(addr['lon'])
                            addr['lat'] = dms_to_decimal(addr['lat'])
                            file_stats['has_own_coords'] += 1
                        except Exception as err:
                            print('Warning:', err, file=sys.stderr)
                            addr['lon'] = ''
                            addr['lat'] = ''
                    # Get lng/lat from faces
                    elif cd_geo in midpoints:
                        addr['lon'] = midpoints[cd_geo][0]
                        addr['lat'] = midpoints[cd_geo][1]
                        file_stats['has_face_coords'] += 1
                    else:
                        addr['lon'] = ''
                        file_stats['missing_coords'] += 1
                        missing_faces.add(cd_geo)

                    # If coords available
                    if addr['lon'] != '':
                        # Apply area to record
                        subdistrict_id = addr['census sector'][0:11]
                        if (subdistrict_id) in admin_areas['subdistrict']:
                            addr.update(admin_areas['subdistrict'][subdistrict_id])
                        else:
                            # Fallback to district
                            district_id = addr['census sector'][0:9]
                            if (district_id) in admin_areas['district']:
                                addr.update(admin_areas['district'][district_id])
                            else:
                                # Fallback to municipality
                                file_stats['missing_municipality'] += 1
                                municipality_id = addr['census sector'][0:7]
                                if (municipality_id) in admin_areas['municipality']:
                                    addr.update(admin_areas['municipality'][municipality_id])

                        # Check if state is present to confirm area was found
                        if 'state' in addr:
                            csv_writer.writerow(addr)
                        else:
                            file_stats['missing_areas'] += 1
                            missing_areas.add(addr['census sector'])


    with open(RESULTS_PATH + '/'+state_id+'-missing_faces.csv', 'w') as missing_faces_file:
        missing_faces_file.writelines(
            "%s\n" % i for i in sorted(missing_faces))

    with open(RESULTS_PATH + '/'+state_id+'-missing_areas.csv', 'w') as missing_areas_file:
        missing_areas_file.writelines(
            "%s\n" % i for i in sorted(missing_areas))

    return file_stats


# Entry point
admin_areas = load_admin_areas()
stats = {}

states_zip = glob.glob(
    FACES_2019_SOURCE + '/**/*_faces_de_logradouros_2019.zip', recursive=True)
for state_zip in states_zip:

    # Clear tmp directory
    tmp_files = glob.glob('/tmp/**/*', recursive=True)
    for tmp_file in tmp_files:
        if os.path.isfile(tmp_file):
            os.remove(tmp_file)

    state_code = os.path.basename(state_zip)[0:2]
    print('Parsing state: ' + state_code)

    [state_id, faces_midpoints] = load_faces_midpoints(state_code, state_zip)

    stats[state_id] = parse_addresses(state_id, faces_midpoints, admin_areas)
    stats[state_id]['state_code'] = state_code

# Write stats
with open(RESULTS_PATH + '/stats.csv', 'w', newline='') as stats_csvfile:
    headers = ['state_id', 'state_code', 'total',
               'missing_coords', 'has_own_coords', 'has_face_coords', 'missing_areas']
    csv_writer = csv.DictWriter(stats_csvfile, headers, extrasaction='ignore')
    csv_writer.writeheader()

    for item_id, v in stats.items():
        v.update({'state_id': item_id})
        csv_writer.writerow(v)
