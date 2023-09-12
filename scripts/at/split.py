# -*- coding: utf-8 -*-

import __future__
import csv, sys, json, copy, datetime, time

def main(address_filename, street_filename):
    timestamp = datetime.datetime.now().strftime('%Y%m%d')

    streets = {}
    with open(street_filename) as f:
        reader = csv.reader(f, delimiter=';')
        next(reader)
        for row in reader:
            streets[row[0]] = row[1].strip()

    writers = {}
    pts = {}
    with open(address_filename) as f:
        reader = csv.reader(f, delimiter=';')
        headers = next(reader) + ['STRASSE']
        for row in reader:
            srs = row[17].strip()
            if not srs in writers:
                writers[srs] = csv.writer(open('at-{}-{}.csv'.format(srs, timestamp), 'w'))
                writers[srs].writerow(headers)
            writers[srs].writerow(row + [streets.get(row[4].strip(), '')])

    template = {}
    with open('at_source.json', 'r') as f:
        template = json.load(f)
    for srs in writers:
        source = copy.deepcopy(template)
        source['data'] = 'https://data.openaddresses.io/cache/at-{}.zip'.format(timestamp)
        source['conform']['srs'] = 'EPSG:{}'.format(srs)
        source['conform']['file'] = 'at-{}-{}.csv'.format(srs, timestamp)
        source['attribution'] = '© Austrian address register, date data from {}'.format(datetime.datetime.now().isoformat().split('T')[0])
        with open('at-{}.json'.format(srs), 'w') as f:
            json.dump(source, f, indent=4)

    print(timestamp)

if __name__ == '__main__':
    main(address_filename=sys.argv[1], street_filename=sys.argv[2])
