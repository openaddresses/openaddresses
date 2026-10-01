#!/usr/bin/env python3
"""Build building-level Japanese addresses from the Address Base Registry (ABR).

Joins, for each prefecture, the 住居表示 residence master (names and numbers,
no coordinates) to its position table (coordinates, IDs only), and adds the
county (郡) and postcode from the town (町字) master. Writes one CSV for the
whole country, zipped.

The ABR CDN only serves Japanese IP addresses, so run this from Japan or over
a VPN. Downloads are cached in the raw directory.

Data: デジタル庁 アドレス・ベース・レジストリ, 公共データ利用規約（第1.0版）
https://www.digital.go.jp/policies/base_registry_address_tos

Usage: python3 abr_residential.py [raw_dir] [output_dir]
"""
import sys
import urllib.request
import zipfile
from pathlib import Path

import duckdb

BASE = "https://data.address-br.digital.go.jp"
OUT_NAME = "jp_abr_residential"


def fetch(url, dest):
    if not dest.exists():
        print(f"downloading {url}", file=sys.stderr)
        tmp = dest.with_suffix(".tmp")
        urllib.request.urlretrieve(url, tmp)
        tmp.rename(dest)
    return dest


def extract(path):
    with zipfile.ZipFile(path) as zf:
        name = zf.namelist()[0]
        dest = path.parent / name
        if not dest.exists():
            zf.extract(name, path.parent)
    return dest


def main():
    raw = Path(sys.argv[1] if len(sys.argv) > 1 else "raw")
    out = Path(sys.argv[2] if len(sys.argv) > 2 else ".")
    raw.mkdir(parents=True, exist_ok=True)
    out.mkdir(parents=True, exist_ok=True)

    town = fetch(f"{BASE}/mt_town/mt_town_all.csv.zip", raw / "mt_town_all.csv.zip")
    city = fetch(f"{BASE}/mt_city/mt_city_all.csv.zip", raw / "mt_city_all.csv.zip")
    rsdt, pos = [], []
    for n in range(1, 48):
        p = f"{n:02d}"
        rsdt.append(fetch(f"{BASE}/mt_rsdtdsp_rsdt/pref/mt_rsdtdsp_rsdt_pref{p}.csv.zip",
                          raw / f"mt_rsdtdsp_rsdt_pref{p}.csv.zip"))
        pos.append(fetch(f"{BASE}/mt_rsdtdsp_rsdt_pos/pref/mt_rsdtdsp_rsdt_pos_pref{p}.csv.zip",
                         raw / f"mt_rsdtdsp_rsdt_pos_pref{p}.csv.zip"))

    con = duckdb.connect()
    read = lambda files: "read_csv([{}], all_varchar=true, union_by_name=true)".format(
        ", ".join(f"'{extract(f)}'" for f in files))

    csv_path = out / f"{OUT_NAME}.csv"
    # The town master has exact duplicate rows, and some residences have two
    # position records; keep one of each so every address appears once.
    con.execute(f"""
        COPY (
            WITH town AS (
                SELECT DISTINCT ON (lg_code, machiaza_id) lg_code, machiaza_id, county, koaza, post_code
                FROM {read([town])}
                ORDER BY lg_code, machiaza_id
            ),
            city AS (
                SELECT DISTINCT ON (lg_code) lg_code, pref, county
                FROM {read([city])}
                ORDER BY lg_code
            ),
            pos AS (
                SELECT DISTINCT ON (lg_code, machiaza_id, blk_id, rsdt_id, coalesce(rsdt2_id, ''))
                    lg_code, machiaza_id, blk_id, rsdt_id, coalesce(rsdt2_id, '') AS rsdt2_id, rep_lon, rep_lat
                FROM {read(pos)}
                WHERE rep_lon IS NOT NULL AND rep_lat IS NOT NULL
                ORDER BY lg_code, machiaza_id, blk_id, rsdt_id, coalesce(rsdt2_id, ''), rep_lon, rep_lat
            )
            SELECT
                r.lg_code || r.machiaza_id || r.blk_id || r.rsdt_id || coalesce(r.rsdt2_id, '') AS id,
                c.pref,
                concat_ws('', coalesce(t.county, c.county), r.city, r.ward) AS city,
                concat_ws('', r.oaza_cho, r.chome) AS street,
                t.koaza,
                concat_ws('-', r.blk_num, r.rsdt_num, r.rsdt_num2) AS number,
                t.post_code AS postcode,
                p.rep_lon AS lon,
                p.rep_lat AS lat
            FROM {read(rsdt)} r
            JOIN pos p
              ON p.lg_code = r.lg_code AND p.machiaza_id = r.machiaza_id AND p.blk_id = r.blk_id
             AND p.rsdt_id = r.rsdt_id AND p.rsdt2_id = coalesce(r.rsdt2_id, '')
            LEFT JOIN town t ON t.lg_code = r.lg_code AND t.machiaza_id = r.machiaza_id
            LEFT JOIN city c ON c.lg_code = r.lg_code
            WHERE r.ablt_date IS NULL
            ORDER BY id
        ) TO '{csv_path}' (HEADER, DELIMITER ',')
    """)
    rows = con.execute(f"SELECT count(*) FROM read_csv('{csv_path}')").fetchone()[0]

    with zipfile.ZipFile(out / f"{OUT_NAME}.csv.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, csv_path.name)
    print(f"wrote {rows} rows to {out / (OUT_NAME + '.csv.zip')}", file=sys.stderr)


if __name__ == "__main__":
    main()
