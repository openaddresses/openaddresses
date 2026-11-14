#!/usr/bin/env python3
"""Download Saarland Hauskoordinaten from the OGC API and build Saarland.zip.

Pages through every feature (the page count comes from numberMatched, so it
keeps up as the dataset grows), takes lon/lat from the WGS84 point geometry,
and writes Saarland.csv inside Saarland.zip.

Usage: python3 saarland.py [output_dir]
"""
import csv
import json
import sys
import time
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

BASE = "https://geoportal.saarland.de/spatial-objects/416/collections/GDI_ALKIS_Gebaeude:Hauskoordinaten/items?f=json"
PAGE = 2500  # server only accepts limits of 1, 5, 10, 20, 50, 100, 200, 500, 1000 or 2500
COLUMNS = [
    "X", "Y", "gml_id", "OBJECTID", "OI", "QUA", "LAN", "RBZ", "KRS", "GMD", "OTT", "SSS",
    "HNR", "XCOORD", "YCOORD", "STN", "PLZ", "ONM", "PSN", "AUD", "ADZ",
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "openaddresses"})
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.load(resp)


def fetch_page(offset, total):
    expected = min(PAGE, total - offset)
    for attempt in range(6):
        try:
            features = get(f"{BASE}&limit={PAGE}&offset={offset}")["features"]
            if len(features) != expected:
                raise ValueError(f"expected {expected} features, got {len(features)}")
            return features
        except Exception as exc:  # retry transient errors and short pages
            print(f"offset {offset} attempt {attempt}: {exc}", file=sys.stderr)
            time.sleep(5 * 2 ** attempt)
    raise RuntimeError(f"failed to fetch offset {offset}")


def row(feature):
    props = feature["properties"]
    lon, lat = feature["geometry"]["coordinates"][:2]
    out = {c: props.get(c) for c in COLUMNS}
    out["X"], out["Y"] = f"{lon:.8f}", f"{lat:.8f}"
    # keep the zero padding of the municipality part/street keys
    if out["OTT"] is not None:
        out["OTT"] = f"{int(out['OTT']):04d}"
    if out["SSS"] is not None:
        out["SSS"] = f"{int(out['SSS']):05d}"
    return out


def main():
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    out_dir.mkdir(parents=True, exist_ok=True)

    total = get(f"{BASE}&limit=1")["numberMatched"]
    print(f"numberMatched: {total}", file=sys.stderr)

    with ThreadPoolExecutor(4) as pool:
        pages = pool.map(lambda off: fetch_page(off, total), range(0, total, PAGE))
        seen = set()
        csv_path = out_dir / "Saarland.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=COLUMNS, lineterminator="\n")
            writer.writeheader()
            for features in pages:
                for feature in features:
                    gml_id = feature["properties"]["gml_id"]
                    if gml_id in seen:
                        continue
                    seen.add(gml_id)
                    writer.writerow(row(feature))

    if len(seen) != total:
        sys.exit(f"wrote {len(seen)} rows but numberMatched is {total}")

    with zipfile.ZipFile(out_dir / "Saarland.zip", "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(csv_path, csv_path.name)
    print(f"wrote {len(seen)} rows to {out_dir / 'Saarland.zip'}", file=sys.stderr)


if __name__ == "__main__":
    main()
