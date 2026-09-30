#!/usr/bin/env python3
"""
Download the two upstream sources needed for the Greece countrywide address build:

1. Hellenic Cadastre "declared streets" point dataset (street name + number, EGSA87),
   compiled from property-owner declarations during national cadastre registration.
2. Ministry of Environment & Energy (YPEN) national municipality boundaries
   ("Kallikratis" administrative divisions), used to assign a city/municipality
   name to each address point via spatial join.

Run with: python3 download.py
Requires: requests (pip install -r requirements.txt)
"""
import pathlib
import sys
import urllib.request

DATA_DIR = pathlib.Path(__file__).parent / "data"

SOURCES = {
    "ogp_hc_regstreets_egsa87.zip": (
        "https://data.gov.gr/dataset/16068541-970c-4d1a-8047-b95fd4d261ba/"
        "resource/946e2a6a-8ab8-4c62-89e3-e14ecd9868a1/download/"
        "ogp_hc_regstreets_egsa87.zip"
    ),
    "kallikratis_dimoi.geojson": (
        "https://wfdservices.ypeka.gr/geoserver/WFD_geodata_50K/wfs"
        "?service=WFS&version=2.0.0&request=GetFeature"
        "&typeNames=WFD_geodata_50K%3Akallikratikoi_dimoi"
        "&outputFormat=application%2Fjson"
    ),
}


def download(name: str, url: str) -> None:
    dest = DATA_DIR / name
    if dest.exists():
        print(f"skip (already downloaded): {name}")
        return
    print(f"fetching {name} ...")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as f:
        f.write(resp.read())
    print(f"  -> {dest} ({dest.stat().st_size:,} bytes)")


def main() -> int:
    DATA_DIR.mkdir(exist_ok=True)
    for name, url in SOURCES.items():
        download(name, url)
    return 0


if __name__ == "__main__":
    sys.exit(main())
