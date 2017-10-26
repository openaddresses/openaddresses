# coding: utf-8

# Download the file from http://geoportal.geoportal-th.de/hausko_umr/HK-TH.zip
# Unzip and run from within the unzipped folder

import csv
import six
reader = csv.reader(open('schluessel-TH.txt'), delimiter=';')
cities = {}
for line in reader:
    if line[0] == 'G':
        cities[tuple(line[1:5])] = line[5]

reader = csv.reader(open('adressen-TH.txt'), delimiter=';')
writer = csv.writer(open('thuringen.txt', 'w'), delimiter=';')
for line in reader:
    city_id = line[3:7]
    city = cities.get(tuple(city_id), '')
    line.append(city)
    writer.writerow(line)
    
