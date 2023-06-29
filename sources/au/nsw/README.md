# statewide
## street/city regexp

Using PSMA Admin Boundaries data obtained with https://github.com/andrewharvey/psma-admin-bdys-data we are able to list all suburb/localities in NSW with:

    ogr2ogr -f CSV -select NAME -where "STATE_PID = '1'" /vsistdout/ Suburbs\ -\ Localities\ -\ MAY\ 2021.shp | tail -n +2 | sort | uniq | sed ':a;N;$!ba;s/\n/|/g'

The output of that is used in the regexp for splitting street names and suburb/localities.

_Administrative Boundaries ©PSMA Australia Limited licensed by the Commonwealth of Australia under [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)._

## Source Cache

Data manually exported via https://portal.spatial.nsw.gov.au/portal/home/item.html?id=d3cf7c7edef14ca18248c6dc5fcaff96
