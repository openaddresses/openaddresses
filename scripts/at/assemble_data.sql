-- Data is released every April and October.
-- Find and download latest source from https://data.bev.gv.at/geonetwork/srv/eng/catalog.search#/search?isTemplate=n&resourceTemporalDateRange=%7B%22range%22:%7B%22resourceTemporalDateRange%22:%7B%22gte%22:null,%22lte%22:null,%22relation%22:%22intersects%22%7D%7D%7D&sortBy=creationDateForResource&sortOrder=desc&from=1&to=50&query_string=%7B%22th_httpinspireeceuropaeutheme-theme_tree.key%22:%7B%22http:%2F%2Finspire.ec.europa.eu%2Ftheme%2Fad%22:true%7D%7D
-- Use the "Adresse Relationale Tabellen Stichtag" version to match this schema
-- Unzip and load duckdb from directory

LOAD spatial;

CREATE temp TABLE addresses AS FROM (
  SELECT 
    a.ADRCD
    , a.HNR_ADR_ZUSAMMEN
    , a.HAUSNRTEXT
    , a.HAUSNRZAHL1
    , a.HAUSNRBUCHSTABE1
    , a.HAUSNRVERBINDUNG1
    , a.HAUSNRZAHL2
    , a.HAUSNRBUCHSTABE2
    , a.HAUSNRBEREICH
    , a.HOFNAME
    , s.STRASSENNAME
    , s.STRASSENNAMENZUSATZ
    , s.SZUSADRBEST
    , s.ZUSTELLORT
    , o.ORTSNAME
    , g.GEMEINDENAME
    , a.PLZ::varchar as PLZ
    , a.EPSG
    , ST_Point(a.HW::double, a.RW::double) AS "geometry"
    , 0.0::double AS "lat"
    , 0.0::double AS "lon"
  FROM 
    'ADRESSE.csv' a
    LEFT JOIN  'STRASSE.csv' s ON a.SKZ = s.SKZ
    LEFT JOIN 'ORTSCHAFT.csv' o ON a.OKZ = o.OKZ
    LEFT JOIN 'GEMEINDE.csv' g ON a.GKZ = g.GKZ
);

-- transform coordinates
UPDATE addresses SET geometry = ST_FlipCoordinates(ST_Transform("geometry", 'EPSG:31254', 'EPSG:4326')) WHERE EPSG = '31254';
UPDATE addresses SET geometry = ST_FlipCoordinates(ST_Transform("geometry", 'EPSG:31255', 'EPSG:4326')) WHERE EPSG = '31255';
UPDATE addresses SET geometry = ST_FlipCoordinates(ST_Transform("geometry", 'EPSG:31256', 'EPSG:4326')) WHERE EPSG = '31256';

-- fix empty data
UPDATE addresses SET HAUSNRBEREICH = NULL WHERE HAUSNRBEREICH = 'keine Angabe';
UPDATE addresses SET lat = ST_Y("geometry"), lon = ST_X("geometry");

-- Export data with
COPY(SELECT * EXCLUDE(EPSG, "geometry") FROM addresses) TO 'AT-addresses.csv';

-- Zip file and upload to OA