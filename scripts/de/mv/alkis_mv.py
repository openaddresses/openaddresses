#!/usr/bin/env python3
import argparse
import datetime as dt
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from os import environ
from pathlib import Path
from zipfile import ZipFile


DATA_URL = (
    "https://www.laiv-mv.de/static/LAIV/Geoinformation/Dateien/Download%20GEOBROKER/"
    "AAA2Shape_LandMV__2026_01_06.zip"
)


def log(message: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {message}", file=sys.stderr)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        print(f"{name} is required.", file=sys.stderr)
        sys.exit(1)


def build_env() -> dict:
    env = dict(environ)
    proj_path = Path("/opt/homebrew/share/proj")
    if proj_path.exists():
        env.setdefault("PROJ_LIB", str(proj_path))
    return env


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


def build_combined_gpkg(input_dir: Path, combined_path: Path) -> None:
    if combined_path.exists():
        combined_path.unlink()
    hausnummer = input_dir / "02341_Hausnummer_P.shp"
    flurstueck = input_dir / "11001_Flurstueck_F.shp"

    if not hausnummer.exists():
        raise FileNotFoundError(f"Missing {hausnummer}")
    if not flurstueck.exists():
        raise FileNotFoundError(f"Missing {flurstueck}")

    env = build_env()
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            str(combined_path),
            str(hausnummer),
            "02341_Hausnummer_P",
        ],
        check=True,
        env=env,
    )
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            "-update",
            "-append",
            str(combined_path),
            str(flurstueck),
            "-dialect",
            "sqlite",
            "-sql",
            "SELECT GMN_TXT, KRS_TXT, ST_Union(geometry) AS geom "
            "FROM \"11001_Flurstueck_F\" GROUP BY GMN_TXT, KRS_TXT",
            "-nlt",
            "MULTIPOLYGON",
            "-nln",
            "flurstueck_dissolved",
        ],
        check=True,
        env=env,
    )


def run_ogr2ogr(datasource: Path, output_csv: Path, sql: str) -> None:
    env = build_env()
    cmd = [
        "ogr2ogr",
        "-f",
        "CSV",
        str(output_csv),
        str(datasource),
        "-dialect",
        "sqlite",
        "-sql",
        sql,
        "-lco",
        "GEOMETRY=AS_XY",
    ]
    subprocess.run(cmd, check=True, env=env)


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

    require_tool("ogr2ogr")

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

    sql = (
        "SELECT h.TEXT AS street, h.HNR AS number, "
        "f.GMN_TXT AS city, f.KRS_TXT AS district, h.geom AS geom "
        "FROM \"02341_Hausnummer_P\" h "
        "LEFT JOIN flurstueck_dissolved f ON ST_Intersects(h.geom, f.geom) "
        "WHERE h.HNR IS NOT NULL AND h.HNR != '' AND h.TEXT IS NOT NULL AND h.TEXT != ''"
    )

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

        combined_path = extract_dir / "combined.gpkg"
        log("Building dissolved flurstueck layer...")
        build_combined_gpkg(extract_dir, combined_path)

        log("Running ogr2ogr...")
        run_ogr2ogr(combined_path, output_csv, sql)

    with ZipFile(output_zip, "w") as zf:
        zf.write(output_csv, output_csv.name)

    log(f"Wrote {output_zip}")


if __name__ == "__main__":
    main()
