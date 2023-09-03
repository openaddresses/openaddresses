#!/usr/bin/python
# -*- coding: utf-8 -*-

import re
import sys
import requests
import json
from shapely.geometry import Polygon, Point


base_url = "http://api.data.mos.ru/v1/datasets/1927/"
dump_filename = "/users/seriozha/Downloads/ru-msk.csv"

s = requests.Session()
outfile = open(dump_filename,'w')

count = int(s.get(base_url + "count").content)

print "Processing " + str(count) + " rows..."

step = 500

outfile.write("GUID,Address,Raion,Housenumber,Unit,Building,CityParsed,StreetParsed,lon,lat\n")


for i in range(25000/step, count / step + 1):
	step_url = base_url + "rows?$top=" + str(step) + "&$orderby=global_id&$skip=" + str(i * step)
	print step_url

	for item in json.loads(s.get(step_url).content):
		cells = item["Cells"]

		export_string = str(cells["global_id"]) + ","

		full_address = cells["ADRES"]
		admArea = cells["AdmArea"]
		house = cells["DMT"]
		korp = cells["KRT"]
		bldg = cells["STRT"]


		if full_address is not None and len(full_address) >0 :
			export_string += '"'+(full_address.replace("\"", "\"\"").encode('utf-8'))+'",'
		else:
			export_string += '"",'

		if admArea is not None and len(admArea) >0 :
			export_string += '"'+str(admArea[0].encode('utf-8'))+'",'
		else:
			export_string += '"",'

		if house is not None and len(house) >0 :
			export_string += '"'+str(house.encode('utf-8'))+'",'
		else:
			export_string += '"",'

		if korp is not None and len(korp) >0 :
			export_string += '"'+str(korp.encode('utf-8'))+'",'
		else:
			export_string += '"",'

		if bldg is not None and len(bldg) >0 :
			export_string += '"'+str(bldg.encode('utf-8'))+'",'
		else:
			export_string += '"",'


		elems = full_address.split(",")

		if bldg is not None and len(bldg) > 0:
			elems.pop()

		if korp is not None and len(korp) > 0:
			elems.pop()

		if house is not None and len(house) > 0:
			elems.pop()

		if len(elems) > 0:
			matchstring = elems[0]
			m = re.search(u'(^(г. )|(г .)|(город )|(деревня )|(посёлок ))(.*)', matchstring)

			# Check if the first field contains
			if m is not None:
				city = matchstring
				elems.pop(0)
			else:
				city = u"г. Москва"

			export_string += '"'+city.strip().encode('utf-8')+'",'

			if len(elems) > 0:
				export_string += '"'+elems.pop().strip().encode('utf-8')+'",'
			else:
				export_string += ','
		else:
			export_string += ',,'

		if "geoData" in cells:
			flat_coords = cells["geoData"]["coordinates"]
			while not isinstance(flat_coords[0], float):
			 	flat_coords = [item for sublist in flat_coords for item in sublist]

			if flat_coords is not None:
				if len(flat_coords) > 4:
					coords = []
					for i in xrange(len(flat_coords) / 2):
						coords.append([flat_coords[i*2], flat_coords[i*2+1]])
					geom = Polygon(coords)
					export_string += str(geom.centroid.x)+','+str(geom.centroid.y)+"\n"
				elif len(flat_coords) > 0:
					export_string += str(flat_coords[0])+','+str(gflat_coords[1])+"\n"
				else:
					export_string += '","\n'
			else:
				export_string += ',\n'
		else:
			export_string += ',\n'

		outfile.write(export_string)

outfile.close()
