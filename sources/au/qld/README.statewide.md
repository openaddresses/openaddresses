# au/qld/statewide

## Addresses
[Property address Queensland - Text data package](https://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={F878C43D-3087-4102-8F28-1CFEA49B34F1}) (this URL will visit the homepage on your vist visit to the site, so click the link a second time to visit the correct page) data is updated weekly on Sunday.

To download the data in an automated fashion you can run the following (replacing USERNAME%40EXAMPLE.com with your email address):

    curl -H 'referer: https://qldspatial.information.qld.gov.au/' 'https://spatial.information.qld.gov.au/arcgis/sharing/servers/370fdcd7a9aa42148d497d06e6accdd1/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%5D&Feature_Format=&Spatial_Reference=&To_Email=USER%40EXAMPLE.COM&Prepackaged_Data_URLs=DP_PROP_LOCATION_INDEX_QLD.zip%3Aundefined&Output_Title=Extract'

You will then receive an email with the data link.

## Parcels
[Queensland Spatial Cadastral Fabric (QSCF) - whole-of-state Queensland - GDA2020](https://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={8FE3F785-2E3F-45D8-A095-CB20A892A5E3})

Similar to addresses to trigger the data request use:

    curl 'https://spatial.information.qld.gov.au/arcgis/sharing/servers/370fdcd7a9aa42148d497d06e6accdd1/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%5D&Feature_Format=&Spatial_Reference=&To_Email=USER%40EXAMPLE.COM&Prepackaged_Data_URLs=DP_QLD_QSCF_WOS_CUR.zip%3Aundefined&Output_Title=Extract'

## Buildings

There are two building datasets available from the Queensland Government, [Building areas - Queensland](https://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={BC24B68C-50D2-41E8-B0AE-FF4EB2913FDA}) which only includes large footprint buildings but has accurate geometries, and [Generated building outlines - Queensland](https://qldspatial.information.qld.gov.au/catalogue/custom/search.page?q=%22Generated%20building%20outlines%20-%20Queensland%22) which includes all buildings but has less accurate geometries. We have selected the latter to provide better coverage.

Since 2026, requesting a full extract reports too many features to download, and hence we used the scripts within `scripts` to identify a mid latitude to split the state into two smaller areas for download.

The two resulting extracts were then combined with

    parallel "unzip {}" ::: QSC_Extracted_Data_*.zip
    ogr2ogr -f OpenFileGDB Generated_building_outlines.gdb first.gdb
    ogr2ogr -f OpenFileGDB -append Generated_building_outlines.gdb second.gdb
    zip -X -r DP_QLD_GENERATED_BUILDING_OUTLINES.zip Generated_building_outlines.gdb
