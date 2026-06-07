from __future__ import annotations

import io
import json
import shutil
import zipfile
from pathlib import Path

import pandas as pd


def extract_geojson_archive(archive_bytes: bytes, destination: Path) -> None:
    """Extract the downloaded ZIP archive into the destination directory."""
    destination.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
        archive.extractall(destination)


def list_geojson_files(directory: Path, excluded_name: str) -> list[Path]:
    """Return GeoJSON files in a directory, excluding known unwanted files."""
    return sorted(
        path
        for path in directory.iterdir()
        if path.suffix == ".geojson" and path.name != excluded_name
    )


def load_json_file(file_path: Path) -> dict:
    """Load a JSON document from disk using UTF-8."""
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_csv(records: list[dict], output_path: Path) -> None:
    """Write the flattened records to a UTF-8 CSV file."""
    dataframe = pd.DataFrame(records)
    dataframe.to_csv(output_path, index=False, encoding="utf-8-sig")


def zip_output_file(input_path: Path, output_path: Path) -> None:
    """Create a ZIP archive containing the generated CSV file."""
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.write(input_path, arcname=input_path.name)


def remove_intermediate_files(archive_path: Path | None, extract_dir: Path) -> None:
    """Remove the source archive and extracted GeoJSON directory when present."""
    if archive_path is not None and archive_path.exists():
        archive_path.unlink()

    if extract_dir.exists():
        shutil.rmtree(extract_dir)
