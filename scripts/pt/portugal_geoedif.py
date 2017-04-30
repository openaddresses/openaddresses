import json
import os.path

# The source data can be obtained by running
# esri2geojson https://inenetw05.ine.pt:6443/arcgis/rest/services/GeoEdif/GEOEDIF_AC25/MapServer/0 pt-azores25.json
# esri2geojson https://inenetw05.ine.pt:6443/arcgis/rest/services/GeoEdif/GEOEDIF_AC26/MapServer/0 pt-azores26.json
# esri2geojson https://inenetw05.ine.pt:6443/arcgis/rest/services/GeoEdif/GEOEDIF_MAD/MapServer/0 pt-madeira.json
# esri2geojson https://inenetw05.ine.pt:6443/arcgis/rest/services/GeoEdif/GEOEDIF_CONT/MapServer/0 pt-continente.json
# In practice the continental dataset is too large (>3M points), so the server fails before returning the count. Forcing esri2geojson to use OIDs does the trick


tmp_dir = "./tmp"
common_db_path = os.path.abspath("./portugal_geoedif.db")
common_csv_path = os.path.abspath("./portugal_geoedif.csv")

small_files = ['pt-azores25','pt-azores26','pt-madeira']
large_files = ['pt-continente']

# Copy the small files to the temp directory
for sf in small_files:
    print "Copying " + sf + "..."
    command = 'cp ' + sf + '.json ' + os.path.join(tmp_dir,sf + '.json')
    os.system(command)

# Spit the large files into chunks
for lf in large_files:
    stream = open(lf + '.json', 'r') 
    
    chunk_size = 100000
    
    header = stream.readline()
    current_chunk = 0
    has_more_lines = True
    while has_more_lines:
        print "Parsing chunk " + str(current_chunk+1) + "..."
        target_path = os.path.join(tmp_dir,lf + '_' + str(current_chunk) + '.json')
        target_file = open(target_path,'wb')
        target_file.write(header)
        current_chunk = current_chunk + 1
        
        for f in xrange(chunk_size):
            feature = stream.readline()
            if feature!=']}':
            	target_file.write(feature)
            else:
                has_more_lines = False
                break
                
        target_file.write("]}")
        target_file.close()


# Build up an SQLite database from all chunks
if os.path.exists(common_db_path):
	os.remove(common_db_path)

for dp, dn, fn in os.walk(tmp_dir):
	for file_name in [ fi for fi in fn if fi.endswith(".json") ]:
		print file_name
		command = 'ogr2ogr -append -f "SQLite" ' + common_db_path + ' ' + os.path.join(tmp_dir,file_name) + ' -t_srs EPSG:4326 -nln portugal_geoedif'
		os.system(command)
	
# Combine the data into a common csv table
print "Converting to csv and packaging as zip"
os.system('ogr2ogr -f CSV ' + common_csv_path + ' ' + common_db_path)
os.system('zip -9 portugal_geoedif.zip ' + common_csv_path)
