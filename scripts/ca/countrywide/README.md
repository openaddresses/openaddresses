# Canada National Address Register (NAR)

Canada's National Address Register can be downloaded from:
https://www150.statcan.gc.ca/n1/pub/46-26-0002/462600022022001-eng.htm
https://www150.statcan.gc.ca/n1/pub/46-26-0002/2022001/2023.zip

## Description

Build a combined CSV of the Statistics Canada National Address Register

The data is distributed in two sets of files, addresses and locations. Both
have a field called LOC_GUID that is used to join the two to attach latitude
and longitude to the addresses.

This script reads all CSVs for both the Addresses and Locations, joins them on
the LOC_GUID, and saves out the addresses with new fields REPPOINT_LATITUDE and
REPPOINT_LONGITUDE leaving all other address fields in place. It also converts
to UTF8 in the process from ISO-8859-1.

## Running

Run `make`. The Python script requires pandas to be installed.
The Makefile will download the file and build the final CSV
