# recreate database
dropdb --if-exists -U postgres nl
createdb -U postgres nl

# create output file & make writeable -- necessary bc postgres will
# be running as the postgres user
touch nl-out.csv && chmod 0777 nl-out.csv

# download & combine data, generate CSV
node nl-data.js && node nl-data.js CSV `pwd`/nl-out.csv
