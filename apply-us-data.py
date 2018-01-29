#!/usr/bin/env python
# -*- coding: utf-8 -*-

import csv, json
from glob import glob
from os.path import basename, join

with open(join('us-data', 'codes.txt')) as f:
    rows = list(csv.DictReader(f, dialect='excel-tab'))
    codes = dict([(row['Postal Code'].lower(), row['State']) for row in rows])

with open(join('us-data', 'states.txt')) as f:
    rows = list(csv.DictReader(f, dialect='excel-tab'))
    states = dict([(row['Name'], row['State FIPS']) for row in rows])

with open(join('us-data', 'counties.txt')) as f:
    counties = dict()

    for row in csv.DictReader(f, dialect='excel-tab'):
        key = row['State FIPS'], row['Name']
        value = row['County FIPS'], row['Name']
        counties[key] = value

        # some key variations
        if row['Name'].endswith(' County'):
            counties[(row['State FIPS'], row['Name'][:-7])] = value
        if row['Name'].endswith(' Parish'):
            counties[(row['State FIPS'], row['Name'][:-7])] = value
        if row['Name'].endswith(' Municipality'):
            counties[(row['State FIPS'], row['Name'][:-13])] = value

    # more key variations
    for ((s, c), value) in list(counties.items()):
        if c.startswith('St. '):
            counties[(s, 'Saint '+c[4:])] = value

    for ((s, c), value) in list(counties.items()):
        counties[(s, c.lower())] = value
        counties[(s, c.replace('-', ' '))] = value
        counties[(s, c.replace('-', ' ').lower())] = value

for path in glob('sources/us/**/*.json'):
    try:
        with open(path) as f:
            data = f.read()
            info = json.loads(data)
    except:
        print path, ' is invalid json'
        raise

    if 'county' not in info.get('coverage', {}):
        continue

    if 'US Census' in info['coverage']:
        continue

    print path, '...'

    prefix = '\n    "coverage": {\n        '
    if prefix + '"' not in data:
        print path, ' is not valid prefix'
        continue

    state_name = codes[info['coverage']['state']]
    state_fips = states[state_name]

    county = info['coverage']['county']

    # if type(county) is list or basename(path)[6:-5] != county.lower().replace(' ', '-'):
    #     continue

    if type(county) is list:
        county_names = [counties[(state_fips, c)] for c in county]
        print info['coverage'], state_fips, state_name, county_names
        continue

    try:
        if u'ñ' in county:
            county_fips, county_name = counties[(state_fips, county.replace(u'ñ', 'n'))]
        else:
            county_fips, county_name = counties[(state_fips, county)]
    except Exception as inst:
        print "  error generating county"
        continue

    geoid = state_fips + county_fips

    census_dict = dict(geoid=geoid, name=county_name, state=state_name)
    census_json = json.dumps(census_dict, sort_keys=True)

    new_data = data.replace(prefix, '{0}"US Census": {1},\n        '.format(prefix, census_json))

    with open(path, 'w') as file:
        file.write(new_data)

