#!/usr/bin/env python
# -*- coding: utf-8 -*-


import time
import requests
import os.path
import lxml.html
import codecs

# API key can be obtained here: http://openstreetgs.stockholm.se/Home/Key
# Choose "WGS84" as the coordinate system
API_KEY = ""
combined_filename = ''

combined_file = codecs.open(combined_filename, "a", encoding='utf-8')
combined_file.write("municipality, postalarea, postalcode, streetname, streetnum, lon, lat\n")

s = requests.Session()

# This gets the list of all street in Stockholm
streets_url = "http://openstreetws.stockholm.se/LvWS-2.2/Lv.asmx/GetStreetNames?apiKey=" + API_KEY + "&streetNamePattern=*&optionalMunicipality=&optionalPostalArea=&optionalPostalCode="
r = s.get(streets_url)

# We query addresses for every street name and save them as csv lines
for street_element in lxml.html.fromstring(r.content).findall('.//streetname'):
	street_name = street_element.text

	print("Processing " + street_name)

	payload = {'apikey': API_KEY, 'municipalityPattern': '*', 'streetName': street_name, 'streetNumPattern': '*', 'postalCodePattern': '*', 'postalAreaPattern': '*', 'includeAddressConnectionsForTrafficTypes': '0'}
	r = s.post("http://openstreetws.stockholm.se/LvWS-2.2/Lv.asmx/GetAddresses", data=payload, headers = {"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"})

	for addr_element in lxml.html.fromstring(r.content).findall('.//address'):
		wkt = addr_element.find('wkt').text
		latlon = wkt[7:len(wkt)-1].split()
		csv = addr_element.find('municipality').text + ',' + addr_element.find('postalarea').text + ',' + addr_element.find('postalcode').text + ',' + addr_element.find('streetname').text + ',' + addr_element.find('streetnum').text + ',' + latlon[0] + ',' + latlon[1] + '\n'
		combined_file.write(csv)

	time.sleep(2)

combined_file.close()
