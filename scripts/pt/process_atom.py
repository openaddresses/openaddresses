#!/usr/bin/env python
# -*- coding: utf-8 -*-

import lxml.html
import os.path
import requests
import zipfile
import unicodecsv as csv
import urlparse

cache_dir = './cache'
out_path = './pt_addresses.csv'

base_url = 'http://inspire.ine.pt/AD/atom/downloadservice_en.xml'


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



base_page = lxml.html.fromstring(requests.get(base_url).content)
base_pattern = 'http://inspire.ine.pt/AD/atom/CDG_AD_BNM'
file_pattern = 'EPSG4326.zip'


for nuts_link in base_page.findall('.//entry/link'):
	nuts_url = nuts_link.attrib['href']
	if nuts_url[0:len(base_pattern)] == base_pattern:
		print 'Caching files from ' + nuts_url
		nuts_page = lxml.html.fromstring(requests.get(nuts_url).content)
		for file_link in nuts_page.findall('.//entry/link'):
			file_url = file_link.attrib['href']
			if file_url.endswith(file_pattern):
				# This is to fix incorrect links in the atom feed for Madeira
				url_lst = list(urlparse.urlparse(file_url))
				url_lst[1] = 'inspire.ine.pt'
				file_url = urlparse.urlunparse(url_lst)
				print file_url
				if not file_already_cached(file_url):
					download_file_to_cache(file_url,512)

print 'All files cached, will begin parsing'

csvfile = open(out_path, 'w')
fieldnames = ['id','street','house','postcode','city','lon','lat']
writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
writer.writeheader()

for cached_file in [ fi for fi in os.listdir(cache_dir) if fi.endswith(".zip")]:
	print 'Parsing ' + cached_file
	postdescriptors = {}
	thoroughfarenames = {}

	with zipfile.ZipFile(cache_file_path(cached_file), 'r') as zip_file:
		zip_page = lxml.html.fromstring(zip_file.read(zip_file.namelist()[0]))
		for pc in zip_page.findall('.//member/postaldescriptor', namespaces={'wfs':'http://schemas.opengis.net/wfs/2.0/wfs.xsd'}):
			pc_id = pc.attrib['gml:id']
			pc_locality = pc.findall('.//text')[0].text
			pc_postcode = pc.find('postcode').text

			postdescriptors[pc_id] = {'pc_locality':pc_locality,'pc_postcode':pc_postcode}

		for tf in zip_page.findall('.//member/thoroughfarename', namespaces={'wfs':'http://schemas.opengis.net/wfs/2.0/wfs.xsd'}):
			tf_id = tf.attrib['gml:id']
			tf_name = tf.findall('.//text')[0].text
			thoroughfarenames[tf_id] = tf_name

		count = 0

		for ad in zip_page.findall('.//member/address', namespaces={'wfs':'http://schemas.opengis.net/wfs/2.0/wfs.xsd'}):
			ad_id = ad.attrib['gml:id']
			ad_pos = ad.findall('.//pos')[0].text.split()

			ad_num = None
			ad_pc = None
			ad_tf = None

			for loc in ad.findall('.//locator//locatordesignator'):
				if ad_num is None and loc.find('type').attrib['xlink:href'] == 'http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/buildingIdentifier':
					ad_num = loc.find('designator').text

			for comp in ad.findall('.//component'):
				comp_ref = comp.attrib['xlink:href'][1:]
				pc_ref = postdescriptors.get(comp_ref)
				if pc_ref is not None and ad_pc is None:
					ad_pc = pc_ref
				tf_ref = thoroughfarenames.get(comp_ref)
				if tf_ref is not None and ad_tf is None:
					ad_tf = tf_ref

			count = count + 1
			writer.writerow({'id':ad_id,'street':ad_tf,'house':ad_num,'postcode':ad_pc['pc_postcode'],'city':ad_pc['pc_locality'],'lon':ad_pos[1],'lat':ad_pos[0]})

		print 'Parsed ' + str(count) + ' rows'


csvfile.close()
