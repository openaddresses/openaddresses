# au/qld/statewide

## Parcels/Addresses
[Cadastral data weekly - whole of State Queensland](https://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={4091CAF1-50E6-4BC3-B3D4-229AA318231A}) data is updated weekly on Sunday.

To download the data in an automated fashion you can run the following (replacing USERNAME%40EXAMPLE.com with your email address):

    curl 'https://spatial.information.qld.gov.au/arcgis/sharing/servers/0c54a850c61240c284e7a0651766a46f/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%5D&Feature_Format=&Spatial_Reference=&To_Email=USER%40EXAMPLE.COM&Prepackaged_Data_URLs=DP_QLD_DCDB_WOS_CUR.zip%3Aundefined&Output_Title=Extract'

You will then receive an email with the download link.

## Buildings

There are two building datasets available from the Queensland Government, [Building areas - Queensland](https://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={BC24B68C-50D2-41E8-B0AE-FF4EB2913FDA}) which only includes large footprint buildings but has accurate geometries, and [Generated building outlines - Queensland](https://qldspatial.information.qld.gov.au/catalogue/custom/search.page?q=%22Generated%20building%20outlines%20-%20Queensland%22) which includes all buildings but has less accurate geometries. We have selected the latter to provide better coverage.

Since 2026, requesting a full extract reports too many features to download, and hence we used the scripts within `scripts` to identify a mid latitude to split the state into two smaller areas for download.

The two resulting extracts were then combined with

    parallel "unzip {}" ::: QSC_Extracted_Data_*.zip
    ogr2ogr -f OpenFileGDB Generated_building_outlines.gdb first.gdb
    ogr2ogr -f OpenFileGDB -append Generated_building_outlines.gdb second.gdb
    zip -X -r DP_QLD_GENERATED_BUILDING_OUTLINES.zip Generated_building_outlines.gdb
