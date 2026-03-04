#!/usr/bin/env python3
import argparse
import datetime as dt
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile


BASE_URL = "https://alkis-vektor-daten.s3.eu-de.cloud-object-storage.appdomain.cloud/"


def log(message: str) -> None:
    ts = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    print(f"[{ts}] {message}", file=sys.stderr)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        print(f"{name} is required.", file=sys.stderr)
        sys.exit(1)


def list_keys() -> list[str]:
    ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
    marker = None
    keys: list[str] = []
    while True:
        url = BASE_URL
        if marker:
            url = f"{BASE_URL}?marker={urllib.parse.quote(marker)}"
        with urllib.request.urlopen(url) as resp:
            data = resp.read()
        root = ET.fromstring(data)
        for entry in root.findall("s3:Contents", ns):
            key = entry.find("s3:Key", ns).text
            if key.endswith(".gpkg.zip"):
                keys.append(key)
        truncated = root.find("s3:IsTruncated", ns)
        if truncated is not None and truncated.text == "true":
            next_marker = root.find("s3:NextMarker", ns)
            marker = next_marker.text if next_marker is not None else keys[-1]
            continue
        break
    return keys


def download(key: str, dest: Path, retries: int = 3) -> None:
    url = f"{BASE_URL}{urllib.parse.quote(key, safe='/')}"
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


def extract_zip(zip_path: Path, dest_dir: Path) -> Path | None:
    with ZipFile(zip_path) as zf:
        zf.extractall(dest_dir)
    for candidate in dest_dir.glob("*.gpkg"):
        return candidate
    return None


def run_ogr2ogr(datasource: Path, output_csv: Path, sql: str) -> None:
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
    subprocess.run(cmd, check=True)


def build_combined_gpkg(gpkg_path: Path, combined_path: Path) -> None:
    if combined_path.exists():
        combined_path.unlink()
    # Copy only gebaeude into a lightweight working GPKG.
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            str(combined_path),
            str(gpkg_path),
            "gebaeude",
        ],
        check=True,
    )
    # Add dissolved flurstuecke layer for faster joins.
    subprocess.run(
        [
            "ogr2ogr",
            "-f",
            "GPKG",
            "-update",
            "-append",
            str(combined_path),
            str(gpkg_path),
            "-dialect",
            "sqlite",
            "-sql",
            "SELECT gem__bez, ST_Union(geom) AS geom FROM flurstuecke GROUP BY gem__bez",
            "-nlt",
            "MULTIPOLYGON",
            "-nln",
            "flurstuecke_dissolved",
        ],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download ALKIS GPKG packages for Niedersachsen and extract addresses."
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output directory (default: scripts/de/ni/output).",
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        default=False,
        help="Resume from a previous run using the state file.",
    )
    parser.add_argument(
        "--state-file",
        default=None,
        help="Path to resume state file (default: output/ni_alkis_state.txt).",
    )
    args = parser.parse_args()

    require_tool("ogr2ogr")

    root_dir = Path(__file__).resolve().parents[3]
    work_dir = Path(__file__).resolve().parent
    out_dir = Path(args.output) if args.output else work_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)

    output_csv = out_dir / "ni_alkis_addresses.csv"
    output_zip = out_dir / "ni_alkis_addresses.csv.zip"
    state_file = Path(args.state_file) if args.state_file else out_dir / "ni_alkis_state.txt"
    processed: set[str] = set()
    total_rows = 0

    if args.resume:
        if state_file.exists():
            processed = {line.strip() for line in state_file.read_text().splitlines() if line.strip()}
        if not output_csv.exists():
            print("Resume requested but output CSV not found.", file=sys.stderr)
            sys.exit(1)
        with output_csv.open("r", encoding="utf-8") as fh:
            total_rows = max(0, sum(1 for _ in fh) - 1)
    else:
        if output_csv.exists():
            output_csv.unlink()
        if output_zip.exists():
            output_zip.unlink()
        if state_file.exists():
            state_file.unlink()

    sql = (
        "SELECT g.bez AS street, g.hnr AS number, "
        "f.gem__bez AS city, ST_PointOnSurface(g.geom) AS geom "
        "FROM gebaeude g "
        "LEFT JOIN flurstuecke_dissolved f ON ST_Intersects(g.geom, f.geom) "
        "WHERE g.hnr IS NOT NULL AND g.hnr != '' AND g.bez IS NOT NULL AND g.bez != ''"
    )

    keys = list_keys()
    if not keys:
        print("No GPKG zip files found in bucket.", file=sys.stderr)
        sys.exit(1)

    with tempfile.TemporaryDirectory(dir=work_dir) as tmp_dir:
        tmp_path = Path(tmp_dir)
        first = not output_csv.exists()
        for key in keys:
            if args.resume and key in processed:
                log(f"Skipping {key} (already processed).")
                continue

            zip_name = Path(key).name
            zip_path = tmp_path / zip_name
            extract_dir = tmp_path / f"extract_{zip_name.replace('.zip','')}"

            log(f"Downloading {key}...")
            download(key, zip_path)

            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir(parents=True, exist_ok=True)

            log(f"Unzipping {zip_name}...")
            gpkg_path = extract_zip(zip_path, extract_dir)
            if gpkg_path is None:
                print(f"No GPKG found in {zip_name}", file=sys.stderr)
                continue

            combined_path = extract_dir / "combined.gpkg"
            log(f"Building dissolved flurstuecke layer for {gpkg_path}...")
            build_combined_gpkg(gpkg_path, combined_path)

            log(f"Running ogr2ogr on {combined_path}...")
            package_csv = extract_dir / "addresses.csv"
            run_ogr2ogr(combined_path, package_csv, sql)

            if not package_csv.exists():
                print(f"Missing CSV output for {gpkg_path}", file=sys.stderr)
                continue

            package_rows = 0
            if first:
                shutil.move(package_csv, output_csv)
                with output_csv.open("r", encoding="utf-8") as fh:
                    package_rows = max(0, sum(1 for _ in fh) - 1)
                first = False
            else:
                with package_csv.open("r", encoding="utf-8") as src, output_csv.open(
                    "a", encoding="utf-8"
                ) as dst:
                    header = src.readline()
                    if not header:
                        continue
                    for line in src:
                        dst.write(line)
                        package_rows += 1
            total_rows += package_rows
            log(f"Total rows so far: {total_rows}")
            with state_file.open("a", encoding="utf-8") as fh:
                fh.write(f"{key}\n")
            processed.add(key)

    with ZipFile(output_zip, "w") as zf:
        zf.write(output_csv, output_csv.name)

    log(f"Wrote {output_zip}")


if __name__ == "__main__":
    main()
