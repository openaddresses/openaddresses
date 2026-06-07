from __future__ import annotations

import argparse
from pathlib import Path

from lib.download import (
    DEFAULT_ARCHIVE_PATH,
    DownloadInstructionsError,
    load_or_download_archive,
)
from lib.fs import (
    extract_geojson_archive,
    list_geojson_files,
    remove_intermediate_files,
    write_csv,
    zip_output_file,
)
from lib.process import collect_records

# ALS provides 3D addresses for public housing estates, we exclude these from processing and only target 2D addresses.
EXCLUDED_FILE = "als_addresses_3d_(public_rental_housing).geojson"
BASE_DIR = Path(__file__).resolve().parent
EXTRACT_DIR = BASE_DIR / "geojson_files"
CSV_FILENAME = BASE_DIR / "hk_countrywide.csv"
ZIP_FILENAME = BASE_DIR / "hk_countrywide.zip"


def parse_args() -> argparse.Namespace:
    """Parse CLI options for the Hong Kong import script."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--keep-intermediate",
        action="store_true",
        help="Keep the source ALS ZIP and extracted GeoJSON files after processing.",
    )
    return parser.parse_args()


def main() -> int:
    """Download, transform, and archive Hong Kong address data."""
    args = parse_args()
    archive_path: Path | None = None

    try:
        print("Attempting to load or download the Hong Kong ALS dataset...")
        archive_bytes, archive_source, archive_path = load_or_download_archive(
            DEFAULT_ARCHIVE_PATH
        )
    except DownloadInstructionsError as exc:
        print(exc)
        return 1

    try:
        print(f"Using {archive_source} archive at\n  {archive_path}")
        extract_geojson_archive(archive_bytes, EXTRACT_DIR)

        geojson_files = list_geojson_files(EXTRACT_DIR, EXCLUDED_FILE)
        records = collect_records(geojson_files)

        if not records:
            print("No valid data found in GeoJSON files.")
            return 1

        write_csv(records, CSV_FILENAME)
        print(f"CSV file has been saved as\n  {CSV_FILENAME}")

        zip_output_file(CSV_FILENAME, ZIP_FILENAME)
        print(f"Zipped file has been saved as\n  {ZIP_FILENAME}")
        return 0
    finally:
        if not args.keep_intermediate:
            remove_intermediate_files(archive_path, EXTRACT_DIR)


if __name__ == "__main__":
    raise SystemExit(main())
