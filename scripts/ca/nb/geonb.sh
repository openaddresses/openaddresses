#!/bin/bash

# requires: postgis unzip parallel curl git zip

set -eu

# set up postgres, directories
TMP=/work/tmp
mkdir $TMP
mkdir $TMP/geonb

echo "
local all postgres trust
local all all trust
host all all 127.0.0.1/32 trust
host all all ::1/128 trust
host replication postgres samenet trust
" > /etc/postgresql/9.6/main/pg_hba.conf

/etc/init.d/postgresql start

echo "CREATE EXTENSION postgis" | psql -U postgres

curl -s 'http://geonb.snb.ca/downloads/gcadb/geonb_gcadb-bdavg_csv.zip' -o $TMP/gcadb.zip
unzip $TMP/gcadb.zip

# clean up temporary files
/etc/init.d/postgresql stop
rm -rf $TMP
