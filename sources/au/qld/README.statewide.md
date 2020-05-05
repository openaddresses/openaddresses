# au/qld/statewide

## Parcels/Addresses
[Cadastral data weekly - whole of State Queensland](http://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={4091CAF1-50E6-4BC3-B3D4-229AA318231A}) data is updated weekly on Sunday.

To download the data in an automated fashion you can run the following (replacing USERNAME%40EXAMPLE.com with your email address):

    curl 'https://gisservices2.information.qld.gov.au/arcgis/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%5D&Feature_Format=&Spatial_Reference=&To_Email=USERNAME%40EXAMPLE.com&Prepackaged_Data_URLs=DP_QLD_DCDB_WOS_CUR.zip%3Aundefined&Output_Title=Extract'

You will then recieve an email with the download link.

