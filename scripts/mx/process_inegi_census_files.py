import json
import requests
import zipfile
import os.path
import time


json_dir = "./output"
cache_dir = "./cache"
tmp_dir = "./tmp"


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


# First we get the URLs of necessary files to be downloaded
# Currently using the JSON files pre-populated by Mapbox, would normally need to scrap the INEGI website for links


relevant_urls = set()

for dp, dn, fn in os.walk(json_dir):
	for file_name in [ fi for fi in fn if fi.endswith(".json") ]:
		file_path = os.path.join(dp, file_name)
		
		if os.stat(file_path).st_size == 0:
			continue
		
		with open(os.path.join(dp, file_name)) as json_file:
			data = json.load(json_file)
    		relevant_urls.add(data["data"])
  
print "There are " + str(len(relevant_urls)) + " files to download."  		

# Filter out the ones that have already been downloaded
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

common_shape_path = os.path.abspath("./mexico_ne.shp")
if os.path.exists(common_shape_path):
	os.remove(common_shape_path)

# Checks the zip file for the presence of address shapefiles and extracts them into a common shapefile (OGR seems to have an issue with appending to csv)
def extract_shapes_from_zip(zip_path):
	with zipfile.ZipFile(zip_path, 'r') as zip_file:
		zip_member_names = zip_file.namelist()
		for shp_name in [ fi for fi in zip_member_names if fi.endswith("ne.shp")]:
			command = 'ogr2ogr -f "ESRI Shapefile" -append ' + common_shape_path + ' /vsizip/' + os.path.abspath(os.path.join(zip_path, shp_name))
			os.system(command)
			
# Recursively extract the shapefiles from a zip file and all the other zipfiles within it			
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


for dp, dn, fn in os.walk(cache_dir):
	for file_name in [ fi for fi in fn if fi.endswith(".zip") ]:
		extract_all_relevant_data_from_zip(os.path.join(dp, file_name))

print "Done with extraction, converting to CSV..."

common_csv_path = os.path.abspath("./mexico_ne.csv")
csv_command = 'ogr2ogr -t_srs EPSG:4326 -f CSV ' + common_csv_path + ' ' + common_shape_path + ' -nln mexico_ne_wgs84 -lco GEOMETRY=AS_XY'
os.system(csv_command)
