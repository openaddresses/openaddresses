#!/usr/bin/env python3
import argparse
import datetime as dt
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd


DATA_URL = (
    "https://www.geodaten-mv.de/dienste/alkis_lds_download?index=0&dataset=edc8b197-5f60-4608-b911-97ca70c12d70&file=AAA2Shape_LandMV.zip&"
)


def log(message: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {message}", file=sys.stderr)


def download(url: str, dest: Path, retries: int = 3) -> None:
    last_error: Exception | None = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(url) as resp, dest.open("wb") as fh:
                shutil.copyfileobj(resp, fh)
            return
        except Exception as exc:  # noqa: BLE001 - retry on transient download errors
            last_error = exc
    if last_error is not None:
        raise last_error


def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    with ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)


def build_addresses_csv(input_dir: Path, output_csv: Path) -> None:
    hausnummer = input_dir / "02341_Hausnummer_P.shp"
    flurstueck = input_dir / "11001_Flurstueck_F.shp"

    if not hausnummer.exists():
        raise FileNotFoundError(f"Missing {hausnummer}")
    if not flurstueck.exists():
        raise FileNotFoundError(f"Missing {flurstueck}")

    points = gpd.read_file(hausnummer)[["TEXT", "HNR", "geometry"]]
    parcels = gpd.read_file(flurstueck)[["GMN_TXT", "KRS_TXT", "geometry"]]

    joined = gpd.sjoin(points, parcels, how="left", predicate="intersects")
    joined = joined[
        joined["HNR"].notna() & (joined["HNR"] != "")
        & joined["TEXT"].notna() & (joined["TEXT"] != "")
    ]

    result = joined.rename(
        columns={"TEXT": "street", "HNR": "number", "GMN_TXT": "city", "KRS_TXT": "district"}
    )
    result["X"] = result.geometry.x
    result["Y"] = result.geometry.y
    result[["street", "number", "city", "district", "X", "Y"]].to_csv(output_csv, index=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ALKIS AAA2Shape data for Mecklenburg-Vorpommern and extract addresses."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: scripts/de/mv/output).",
    )
    parser.add_argument(
        "--url",
        default=DATA_URL,
        help="Source ZIP URL (note: date-based and must be updated manually).",
    )
    parser.add_argument(
        "--zip",
        default=None,
        help="Path to a local ZIP file to use instead of downloading.",
    )
    args = parser.parse_args()

    work_dir = Path(__file__).resolve().parent
    out_dir = Path(args.output) if args.output else work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    output_csv = out_dir / "mv_alkis_addresses.csv"
    output_zip = out_dir / "mv_alkis_addresses.csv.zip"
    for path in (output_csv, output_zip):
        if path.exists():
            path.unlink()

    url = args.url
    zip_name = Path(urllib.parse.urlparse(url).path).name or "mv_alkis.zip"

    with tempfile.TemporaryDirectory(dir=work_dir) as tmp_dir:
        tmp_path = Path(tmp_dir)
        zip_path = tmp_path / zip_name
        extract_dir = tmp_path / "extract"

        if args.zip:
            local_zip = Path(args.zip).expanduser().resolve()
            if not local_zip.exists():
                print(f"Local ZIP not found: {local_zip}", file=sys.stderr)
                sys.exit(1)
            log(f"Using local ZIP {local_zip}...")
            shutil.copyfile(local_zip, zip_path)
        else:
            log(f"Downloading {url} (manual update required when URL changes)...")
            download(url, zip_path)

        log(f"Unzipping {zip_name}...")
        extract_zip(zip_path, extract_dir)

        log("Joining house numbers to parcels...")
        build_addresses_csv(extract_dir, output_csv)

    with ZipFile(output_zip, "w") as zf:
        zf.write(output_csv, output_csv.name)

    log(f"Wrote {output_zip}")


if __name__ == "__main__":
    main()
