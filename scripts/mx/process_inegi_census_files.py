#!/usr/bin/env python
# -*- coding: utf-8 -*- 

import json
import zipfile
import os.path
import lxml.html
import time
import requests
import csv
import dryscrape
import random
import re
from unidecode import unidecode


json_dir = "./output"
cache_dir = "./cache"
tmp_dir = "./tmp"

inegi_base_url = 'http://buscador.inegi.org.mx'

# Returns the path where a file should be cached
def cache_file_path(url):
	return os.path.join(cache_dir, os.path.basename(url))

# Returns True if we have a valid (i.e. completely downloaded) file already cached. If a file is damaged it is removed.
def file_already_cached(url):
	local_path = cache_file_path(url)
	
	if not os.path.exists(local_path):
		return False
	
	file_ok = True
	try:
		with zipfile.ZipFile(local_path, 'r') as zip_file:
			file_ok = zip_file.testzip() is None
	except:
		file_ok = False
	
	if not file_ok:
		os.remove(local_path)
		
	return file_ok
	
# Downloads a file to cache
def download_file_to_cache(url, chunk_size):
	response = requests.get(url, stream=True)
	with open(cache_file_path(url), "wb") as cached_file:
		for chunk in response.iter_content(chunk_size = chunk_size):
			cached_file.write(chunk)


# First we parse the main page of the INEGI website to get the relevant files to download
# To skip loading almost 4000 pages (the website is slow and not very reliable) we build the zipfile URLs based on a naming schema
# For that we need the (normalized) name of the state, so we search and process the links by state
# We also use the urban/rural distinction and the numeric code of the file, both are available from the search results page


relevant_urls = set()

s = dryscrape.Session()
s.visit(inegi_base_url + '/search?client=ProductosR&proxystylesheet=ProductosR&getfields=*&sort=meta:edicion:D:E:::D&entsp=a__inegi_politica_p72&lr=lang_es%7Clang_en&oe=UTF-8&ie=UTF-8&entqr=3&filter=0&ip=10.152.21.8&site=ProductosBuscador&tlen=260&ulang=en&access=p&entqrm=0&ud=1&num=10&q=N%C3%BAmeros+Exteriores+inmeta:Tema%3DCartograf%C3%ADa%2520Geoestad%C3%ADstica&dnavs=inmeta:Tema%3DCartograf%C3%ADa%2520Geoestad%C3%ADstica')
s.at_xpath('.//ul[@id="attr_2"]//li[@id="attr_2_more_less"]/a').click() # This expands the list of states, needs to be 'clicked' twice
s.at_xpath('.//ul[@id="attr_2"]//li[@id="attr_2_more_less"]/a').click()
page = lxml.html.fromstring(s.body())

inegi_step_size = 800

for link in page.findall('.//ul[@id="attr_2"]//li[@class="dn-attr-v"]'):
	ref = link.find('div/a')
	state_name = ref.text
	state_name_norm = 'distrito_federal' if state_name == u'Ciudad de México' else unidecode(state_name).encode('ascii').replace(' ','_')
	state_link = ref.attrib['href']
	state_muni_count = int(link.find('span').text[1:-1])
	
	print "Processing " + state_name + ' (' + str(state_muni_count) + ' municipalities)...'
	
	for p in range((state_muni_count - 1) / inegi_step_size + 1):
		page_url = inegi_base_url + state_link + '&num=' + str(inegi_step_size) + '&start=' + str(p * inegi_step_size)
		s.visit(page_url)
		page = lxml.html.fromstring(s.body())
		
		for link in page.findall('.//div[@class="main-results"]/a[@href]'):
			source_url = link.attrib['href']
			urban = 'urbana' if 'Urbana' in link.find('span/span').text_content() else 'rural'
			zip_url = 'http://internet.contenidos.inegi.org.mx/contenidos/Productos/prod_serv/contenidos/espanol/bvinegi/productos/geografia/'+ urban + '/SHP_2/' + state_name_norm + '/' + source_url[-12:] + '_s.zip'
			relevant_urls.add(zip_url)		

print "There are " + str(len(relevant_urls)) + " files to download."  		

# Filter out the files that have already been downloaded
urls_to_download = filter(lambda x: not file_already_cached(x), relevant_urls)

# Attempt to download all the files one by one (not to overload the server, multiple streams result in many 403 responses)
# Progressively decrease the chunk size which increases reliability of downloads at the expense of speed
chunk_size = 512

while len(urls_to_download) > 0:
	url_count = len(urls_to_download)
	print str(url_count) + " files remain to be cached..."

	i = 0
	for url in urls_to_download:
		i = i + 1
		print "Downloading " + os.path.basename(url) + " [" + str(i) + "/" + str(url_count) + "]"
		download_file_to_cache(url, chunk_size)
		time.sleep(2)
	
	chunk_size = max(chunk_size / 2, 1)
	urls_to_download = filter(lambda x: not file_already_cached(x), urls_to_download)
	time.sleep(10)


print "All files are cached, building the common data source"



# Once all the zip files are cached, we process them recursively and put the data into an temporary SQLite database
common_db_path = os.path.abspath("./mexico_ne.db")

if os.path.exists(common_db_path):
	os.remove(common_db_path)

# Add a table providing municipality details (from http://www.conabio.gob.mx/informacion/gis/maps/geo/loc2010gw.zip)
# More details at http://www.conabio.gob.mx/informacion/metadata/gis/loc2010gw.xml?_xsl=/db/metadata/xsl/fgdc_html.xsl&_indent=no
os.system('ogr2ogr -f "SQLite" ' + common_db_path + ' "' + os.path.abspath("./loc2010gw.shp") + '" -nln loc2010')

# Checks the zip file for the presence of address shapefiles and extracts them into a common shapefile (OGR seems to have an issue with appending to csv)
def extract_shapes_from_zip(zip_path):
	with zipfile.ZipFile(zip_path, 'r') as zip_file:
		zip_member_names = zip_file.namelist()
		for shp_name in [ fi for fi in zip_member_names if fi.endswith("ne.shp")]:
			print shp_name
			command = 'ogr2ogr -append -f "SQLite" ' + common_db_path + ' -sql "select *, \'' + shp_name[-15:-6] + '\' as loc from \\"' + shp_name[-15:-4] +'\\"" /vsizip/' + os.path.abspath(os.path.join(zip_path, shp_name)) + ' -t_srs EPSG:4326 -nln mexico_ne'
			os.system(command)
			
# Recursively extracts the shapefiles from a zip file and all the other zipfiles within it			
def extract_all_relevant_data_from_zip(zip_path):
	print "Extracting from " + zip_path
	extract_shapes_from_zip(zip_path)
	with zipfile.ZipFile(zip_path, 'r') as zip_file:
		zip_member_names = zip_file.namelist()
		for zipped_zip in [ fi for fi in zip_member_names if fi.endswith(".zip")]:
			zip_file.extract(zipped_zip,tmp_dir)
			temp_path = os.path.join(tmp_dir, zipped_zip)
			extract_all_relevant_data_from_zip(temp_path)
			os.remove(temp_path)

# Walk through all the cached zip files
for dp, dn, fn in os.walk(cache_dir):
	for file_name in [ fi for fi in fn if fi.endswith(".zip") ]:
		extract_all_relevant_data_from_zip(os.path.join(dp, file_name))


print "Done with extraction, converting to CSV..."

# Convert to CSV and zip
common_csv_temp_path = os.path.abspath("./mexico_ne.tmp.csv")
common_csv_path = os.path.abspath('./mexico_ne.csv')
os.system('ogr2ogr -f CSV ' + common_csv_temp_path + ' ' + common_db_path + ' -sql "select a.*, nom_ent, nom_mun, nom_loc from mexico_ne a left join (select loc, m.nom_ent, m.nom_mun, nom_loc from (select loc, substr(\'0\' || loc,length(loc)-7, 9) loc, substr(\'0\' || loc,length(loc)-7, 5) mun from ( select distinct loc from mexico_ne) b) natural left join (select distinct nom_ent, nom_mun, cve_edo || cve_mun as mun from loc2010) m natural left join loc2010 l where l.cve_loc is null or (loc = l.cve_edo || l.cve_mun || l.cve_loc)) a using (loc)" -lco GEOMETRY=AS_XY')

numeric_pattern = u'(?:[^\W\d_]{,2}[\d]+[^\W\d_]{,2}[\-\u2013\./][^\W\d_]{,2}[\d]+[^\W\d_]{,2}|[\d]*[^\W\d_][\d]*(?:[\-\u2013\./ ]|\s[\-\u2013/]\s)?[^\W\d_]?[\d]+[^\W\d_]?|[^\W\d_]?[\d]+[^\W\d_]?(?:[\-\u2013\./ ]|\s[\-\u2013/]\s)?[\d]*[^\W\d_][\d]*|[\d]+|[^\W\d_](?:(?:[\-\u2013/][^\W\d_])|(?:[\-\u2013\./][^\W\d_]?[\d]+[^\W\d_]?))?)'

number_phrase_pattern = u'(?:(?:№|númro|númr|número|núm.ro|núm|nº|n°|numro|numr|numero|num.ro|num|nrº|nr°|nro|nr.º|nr.°|nr|no|nmrº|nmr°|nmro|nmr.º|nmr.°|nmr.o|n.º|n.°|n.ro|#)\s*)?'

supermanzana_regex = re.compile(u'(?:supermanzana|super mz|super manzana|sm|s.m.|s.m|s m)(?:\s+{})?\s*{}\\b'.format(number_phrase_pattern, numeric_pattern), re.I | re.U)

manzana_regex = re.compile(u'(?:manzana|mza\.?|mz\.?)(?:\s+{})?\s*{}\\b'.format(number_phrase_pattern, numeric_pattern), re.I | re.U)

lote_regex = re.compile(u'(?:lote|lte\.?|lt\.?|l\.?)(?:\s+{})?\s*{}\\b'.format(number_phrase_pattern, numeric_pattern), re.I | re.U)

sin_numero_regex = re.compile('s\.?\s*\/?\s*n\.?', re.I)

temp_csv = open(common_csv_temp_path)
reader = csv.reader(temp_csv)
out = open(common_csv_path, 'w')
writer = csv.writer(out)
headers = reader.next()
numext_index = headers.index('numext')
observ_index = headers.index('observ')

writer.writerow(headers)
for row in reader:
    numext = row[numext_index]
    observ = row[observ_index]
    stripped = supermanzana_regex.sub('', observ)
    stripped = manzana_regex.sub('', stripped)
    stripped = lote_regex.sub('', stripped)
    if observ.strip() and not stripped.strip():
        if not sin_numero_regex.match(numext.strip()):
            numext = numext + ' ' + observ.strip()
        else:
            numext = observ.strip()
        row[numext_index] = numext
        row[observ_index] = ''
    writer.writerow(row)

out.flush()
out.close()
temp_csv.close()
os.remove(common_csv_temp_path)
os.system('zip -9 -j mexico_ne.zip ' + common_csv_path)
