# au/qld/statewide

## Parcels/Addresses
[Cadastral data weekly - whole of State Queensland](http://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={4091CAF1-50E6-4BC3-B3D4-229AA318231A}) data is updated weekly on Sunday.

To download the data in an automated fashion you can run the following (replacing USERNAME%40EXAMPLE.com with your email address):

    curl 'https://spatial.information.qld.gov.au/arcgis/sharing/servers/0c54a850c61240c284e7a0651766a46f/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%5D&Feature_Format=&Spatial_Reference=&To_Email=USER%40EXAMPLE.COM&Prepackaged_Data_URLs=DP_QLD_DCDB_WOS_CUR.zip%3Aundefined&Output_Title=Extract'

You will then receive an email with the download link.

## Buildings

[Building areas - Queensland](http://qldspatial.information.qld.gov.au/catalogue/custom/detail.page?fid={BC24B68C-50D2-41E8-B0AE-FF4EB2913FDA})

    curl 'https://spatial.information.qld.gov.au/arcgis/sharing/servers/0c54a850c61240c284e7a0651766a46f/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob?f=json&env%3AoutSR=102100&Layers_to_Clip=%5B%22Generated%20building%20outlines%22%5D&Feature_Format=File%20Geodatabase%20-%20GDB%20-%20.gdb&Spatial_Reference=Same%20As%20Input&To_Email=USER%40EXAMPLE.COM&Prepackaged_Data_URLs=&Output_Title=Extract'

You will then receive an email with the download link.
