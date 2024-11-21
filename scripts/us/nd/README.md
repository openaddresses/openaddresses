This data is a pain to generate.  I've not figured out an easy way to script it but the basic problem is that there are request problems with the ESRI source.  The machine and pyesridump are unable to load the data with the request timing out after the first 2000 results.  I was able to get the 3rd and 4th 1k result batches passing `-p "WHERE=OBJECTID_12 > 2092"` to pyesridump with the request timing out again, where `2092` is the last `OBJECTID_12` in the result from the first run.  If you're keeping score, 4000 results have been dumped so far.  I did this approach 2 more times adjusting the `OBJECTID_12` value to how far pyesridump managed to get.  I expected to have to do this 9 total times (~17k total records) but, inexplicably, the requests no longer timed out on the 5th run (`-p "WHERE=OBJECTID_12 > 8497"`) with 8733 records being dumped.

I tried running a locally-modified pyesridump that institutes a pause between requests and it still times out after 2 requests, even with a pause of 5 minutes.  I also made these attempts over the course of almost a week so temporary network glitches don't seem to be the source of the problem.

Here are the rough steps:

```
esri2geojson -v https://c39gisserver.co.richland.nd.us/arcgis/rest/services/Cadastre/Parcel_Layer/MapServer/0 richland.geojson.1
tail -1 richland.geojson.1 | egrep -o '"RICHLAND.DBO.RC_Parcels.OBJECTID_12": ([^,]+)'
esri2geojson -p "WHERE=OBJECTID_12 > 2092" -v https://c39gisserver.co.richland.nd.us/arcgis/rest/services/Cadastre/Parcel_Layer/MapServer/0 richland.geojson.2
tail -1 richland.geojson.2 | egrep -o '"RICHLAND.DBO.RC_Parcels.OBJECTID_12": ([^,]+)'
esri2geojson -p "WHERE=OBJECTID_12 > 4221" -v https://c39gisserver.co.richland.nd.us/arcgis/rest/services/Cadastre/Parcel_Layer/MapServer/0 richland.geojson.3
tail -1 richland.geojson.3| egrep -o '"RICHLAND.DBO.RC_Parcels.OBJECTID_12": ([^,]+)'
esri2geojson -p "WHERE=OBJECTID_12 > 6392" -v https://c39gisserver.co.richland.nd.us/arcgis/rest/services/Cadastre/Parcel_Layer/MapServer/0 richland.geojson.4
tail -1 richland.geojson.4| egrep -o '"RICHLAND.DBO.RC_Parcels.OBJECTID_12": ([^,]+)'
esri2geojson -p "WHERE=OBJECTID_12 > 8497" -v https://c39gisserver.co.richland.nd.us/arcgis/rest/services/Cadastre/Parcel_Layer/MapServer/0 richland.geojson.5
```

Then there is some concatenating and file modification to get all 5 files into one richland.geojson file.
