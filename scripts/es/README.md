# Spanish Cadastral Import Script

Spain released their cadastral data as 1700+ GML files. This is too unwieldy for openaddresses' `conform` process to handle efficiently; worse, the GML uses XLINK in a way that `ogr2ogr` can't handle properly.

This code follows these steps:
1. Download ATOM XML files
2. Extract URLs of zipped GML files from the ATOM
3. Fetch zipped GML files
4. For each zipped GML file, uncompress, build an index of XLINK targets (admin boundary, postcode, street name) then traverse the GML, composing an openaddresses-like CSV of the result
5. strip headers from CSVs and combine into a single country-wide CSV

This final CSV is what now lives in the https://data.openaddresses.io/cache/es.zip file. OpenAddresses' `es.json` source processes and reprojects it as usual.

This Makefile was written as work was being done in the terminal. It is intended as a guide for a developer wishing to update Spanish data or replicate the process. It is not guaranteed to run flawlessly -- indeed, some manual correction of malformed URLs in the source ATOM is likely to be necessary. It should get you most of the way there, however.
