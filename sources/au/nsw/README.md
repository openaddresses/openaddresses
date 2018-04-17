Using PSMA Admin Boundaries data obtained with https://github.com/andrewharvey/psma-admin-bdys-data we are able to list all suburb/localities in NSW with:

    ogr2ogr -f CSV -select NAME -where "STATE_PID = '1'" /vsistdout/ Suburbs\ -\ Localities\ FEBRUARY\ 2018.shp | tail -n +2 | sort | uniq | sed ':a;N;$!ba;s/\n/|/g'

_Administrative Boundaries ©PSMA Australia Limited licensed by the Commonwealth of Australia under [Creative Commons Attribution 4.0 International licence (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)._


