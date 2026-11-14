#!/usr/bin/env python3
"""
Join the Hellenic Cadastre declared-streets points (street name + number only)
against the national Kallikratis municipality boundaries to attach a city name
to every address point, then write a single zipped CSV ready to rehost.

Both source layers are natively in EPSG:2100 (Greek Grid / GGRS87), so no
reprojection is needed for the spatial join itself; output coordinates are
reprojected to WGS84 (EPSG:4326) since that's what OpenAddresses expects.

Run with: python3 combine.py
Requires: duckdb (with the spatial extension, auto-installed on first run)
"""
import pathlib
import sys
import zipfile

import duckdb

HERE = pathlib.Path(__file__).parent
DATA_DIR = HERE / "data"
OUT_DIR = HERE / "out"

STREETS_ZIP = DATA_DIR / "ogp_hc_regstreets_egsa87.zip"
STREETS_SHP = DATA_DIR / "streets" / "HC_RegStreets_EGSA87.shp"
DIMOI_GEOJSON = DATA_DIR / "kallikratis_dimoi.geojson"

CSV_NAME = "gr_countrywide_addresses.csv"
ZIP_NAME = "gr_countrywide_addresses.csv.zip"


def unzip_streets() -> None:
    if STREETS_SHP.exists():
        return
    dest = STREETS_SHP.parent
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(STREETS_ZIP) as zf:
        zf.extractall(dest)


def combine() -> pathlib.Path:
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / CSV_NAME

    con = duckdb.connect()
    con.execute("INSTALL spatial; LOAD spatial;")
    con.execute(f"CREATE TABLE dimoi AS SELECT * FROM ST_Read('{DIMOI_GEOJSON}')")
    con.execute(f"""
        CREATE TABLE addr AS
        SELECT *,
            ST_Transform(geom, 'EPSG:2100', 'EPSG:4326', always_xy := true) AS geom_wgs84
        FROM ST_Read('{STREETS_SHP}')
    """)

    con.execute(f"""
        COPY (
            SELECT
                a.ADDRESS AS "STREET",
                a.NUM AS "NUMBER",
                d.lektiko AS "CITY",
                d.kalcode AS "MUN_CODE",
                ST_X(a.geom_wgs84) AS "LON",
                ST_Y(a.geom_wgs84) AS "LAT"
            FROM addr a
            LEFT JOIN dimoi d ON ST_Within(a.geom, d.geom)
        ) TO '{csv_path}' (HEADER, DELIMITER ',')
    """)

    total, matched = con.execute(f"""
        SELECT count(*), count("CITY")
        FROM read_csv('{csv_path}', header=true, quote='"')
    """).fetchone()
    print(f"wrote {csv_path} ({total:,} rows, {matched:,} matched to a municipality)")
    if matched != total:
        print(f"WARNING: {total - matched:,} rows did not match any municipality polygon")
    return csv_path


def package(csv_path: pathlib.Path) -> pathlib.Path:
    zip_path = OUT_DIR / ZIP_NAME
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, arcname=csv_path.name)
    print(f"wrote {zip_path} ({zip_path.stat().st_size:,} bytes)")
    return zip_path


def main() -> int:
    if not STREETS_ZIP.exists() or not DIMOI_GEOJSON.exists():
        print("Missing input data — run download.py first.", file=sys.stderr)
        return 1
    unzip_streets()
    csv_path = combine()
    package(csv_path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
