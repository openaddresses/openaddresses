#!/bin/python

import os
import unicodecsv as csv

writer = csv.DictWriter(open('no.csv', 'w'), fieldnames=('X','Y','PUNKT','KOMM','OBJTYPE','GATENR','GATENAVN','HUSNR','BOKST','POSTNR','POSTNAVN','TRANSID'))
writer.writeheader()
for f in os.listdir('./csv'):
    print(f)
    with open('./csv/{}'.format(f)) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            writer.writerow(row)
