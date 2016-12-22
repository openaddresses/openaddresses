The source of this data is http://www.arcgis.com/home/webmap/viewer.html?webmap=aebf050394024cf3befac2806b775efe&extent=-117.9517,45.8207,-116.448,46.5716

Rather than make individual calls for parcel data, this source downloads the entire compressed blob of features when the map initially loads.  It's not in a nice geojson format either, so to make it that way, run `npm i; node index` which takes the various features in the various layers and puts them into a single featureCollection.  This will dump the data to a file named `asotin.geojson`.   
