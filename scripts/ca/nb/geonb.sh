#!/bin/bash

# requires: postgis unzip parallel curl git zip

set -eu

# set up postgres, directories
WORKDIR=/work
TMP=$WORKDIR/tmp
mkdir $TMP

echo "
local all postgres trust
local all all trust
host all all 127.0.0.1/32 trust
host all all ::1/128 trust
host replication postgres samenet trust
" > /etc/postgresql/9.6/main/pg_hba.conf

/etc/init.d/postgresql start

echo "
    CREATE DATABASE geonb WITH ENCODING 'UTF8';
" | psql -U postgres

echo "
    CREATE EXTENSION postgis
" | psql -U postgres geonb

curl -s 'http://geonb.snb.ca/downloads/gcadb/geonb_gcadb-bdavg_csv.zip' -o $TMP/gcadb.zip
unzip $TMP/gcadb.zip -d $TMP/

rm $TMP/gcadb.zip

echo "
    CREATE TABLE coordinate_classes (cd BIGINT, name_e TEXT, name_f TEXT, status_cd TEXT);
    CREATE TABLE coordinate_methods (cd BIGINT, name_e TEXT, name_f TEXT, status_cd TEXT);
    CREATE TABLE coordinate_sources (cd BIGINT, name_e TEXT, name_f TEXT, status_cd TEXT);
    CREATE TABLE counties (cd BIGINT, name TEXT);
    CREATE TABLE locations (
        id BIGINT,
        pi_par_pid BIGINT,
        county_cd BIGINT,
        pln_cd BIGINT,
        st_type_cd BIGINT,
        street_dir_cd BIGINT,
        civic_NUM TEXT,
        civic_num_suff TEXT,
        street_name TEXT,
        coordinate_class_cd BIGINT,
        coordinate_method_cd BIGINT,
        coordinate_source_cd BIGINT,
        x_coordinate NUMERIC,
        y_coordinate NUMERIC,
        unit_type_cd BIGINT,
        unit_id BIGINT,
        floor BIGINT
    );
    CREATE TABLE place_names (cd BIGINT, name_e TEXT, name_f TEXT, status_cd TEXT);
    CREATE TABLE street_directions (cd BIGINT, name_e TEXT, name_f TEXT, short_name_e TEXT, short_name_f TEXT);
    CREATE TABLE street_types (cd BIGINT, name TEXT, lang_cd BIGINT, display_before_name_flag BIGINT, insupd_name TEXT, short_name TEXT, status_cd BIGINT);
    CREATE TABLE unit_types (cd BIGINT, name_e TEXT, name_f TEXT, status_cd BIGINT);
" | psql -U postgres geonb

iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/coordinate_classes.txt > $TMP/geonb_gcadb-bdavg_csv/coordinate_classes.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/coordinate_methods.txt > $TMP/geonb_gcadb-bdavg_csv/coordinate_methods.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/coordinate_sources.txt > $TMP/geonb_gcadb-bdavg_csv/coordinate_sources.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/counties.txt > $TMP/geonb_gcadb-bdavg_csv/counties.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/locations.txt > $TMP/geonb_gcadb-bdavg_csv/locations.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/place_names.txt > $TMP/geonb_gcadb-bdavg_csv/place_names.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/street_directions.txt > $TMP/geonb_gcadb-bdavg_csv/street_directions.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/street_types.txt > $TMP/geonb_gcadb-bdavg_csv/street_types.txtutf
iconv -f latin1 -t utf-8//TRANSLIT $TMP/geonb_gcadb-bdavg_csv/unit_types.txt > $TMP/geonb_gcadb-bdavg_csv/unit_types.txtutf

echo "
    update pg_database set encoding = pg_char_to_encoding('UTF8') where datname = 'geonb';
" | psql -U postgres

echo "
    COPY coordinate_classes FROM '$TMP/geonb_gcadb-bdavg_csv/coordinate_classes.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY coordinate_methods FROM '$TMP/geonb_gcadb-bdavg_csv/coordinate_methods.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY coordinate_sources FROM '$TMP/geonb_gcadb-bdavg_csv/coordinate_sources.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY counties FROM '$TMP/geonb_gcadb-bdavg_csv/counties.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY locations FROM '$TMP/geonb_gcadb-bdavg_csv/locations.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY place_names FROM '$TMP/geonb_gcadb-bdavg_csv/place_names.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY street_directions FROM '$TMP/geonb_gcadb-bdavg_csv/street_directions.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY street_types FROM '$TMP/geonb_gcadb-bdavg_csv/street_types.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
    COPY unit_types FROM '$TMP/geonb_gcadb-bdavg_csv/unit_types.txtutf' HEADER CSV DELIMITER E'\t' QUOTE E'\b' ENCODING 'UTF8';
" | psql -U postgres geonb

echo "
    DELETE FROM locations WHERE civic_num IS NULL OR civic_num = '0';
" | psql -U postgres

echo "
    CREATE TABLE final AS
        SELECT
            l.id AS id,
            l.pi_par_pid AS  pid,
            l.civic_num||COALESCE(l.civic_num_suff,'') AS number,
            CASE
                WHEN street_types.lang_cd = 1 THEN
                    trim(concat_ws(' ', street_name, street_types.name, street_directions.name_e))
                ELSE
                    trim(concat_ws(' ', street_types.name, street_name, street_directions.name_f))
            END AS street,
            unit_id AS unit_id,
            floor AS floor,
            counties.name AS district,
            CASE
                WHEN place_names.name_e = place_names.name_f THEN
                    place_names.name_e
                WHEN street_types.lang_cd = 1 THEN
                    place_names.name_e||','||place_names.name_f
                WHEN  street_types.lang_cd = 0 THEN
                    place_names.name_f||','||place_names.name_e
            END AS place,
            ST_Transform(ST_SetSRID(ST_Point(x_coordinate, y_coordinate), 2953), 4326) AS geom
        FROM
            locations l
            INNER JOIN counties ON l.county_cd = counties.cd
            INNER JOIN place_names ON l.pln_cd = place_names.cd
            LEFT JOIN street_directions ON l.street_dir_cd = street_directions.cd
            LEFT JOIN street_types ON l.st_type_cd = street_types.cd;
" | psql -U postgres geonb

echo "
    ALTER TABLE final ADD COLUMN x NUMERIC;
    ALTER TABLE final ADD COLUMN y NUMERIC;

    UPDATE final
        SET
            x = ST_X(geom),
            y = ST_Y(geom);
" | psql -U postgres geonb

echo "
    COPY final (number, street, place, district, x, y) TO '$WORKDIR/output.csv' WITH CSV HEADER;
" | psql -U postgres geonb

# clean up temporary files
/etc/init.d/postgresql stop
rm -rf $TMP
