from __future__ import annotations

from pathlib import Path

from lib.fs import load_json_file


def collect_records(files: list[Path]) -> list[dict]:
    """Collect flattened records from all provided GeoJSON files."""
    records: list[dict] = []
    for file_path in files:
        records.extend(load_records_from_geojson(file_path))
    return records


def load_records_from_geojson(file_path: Path) -> list[dict]:
    """Load and flatten all records from a single GeoJSON file."""
    geojson_data = load_json_file(file_path)
    return [
        feature_to_record(feature)
        for feature in geojson_data.get("features", [])
    ]


def feature_to_record(feature: dict) -> dict:
    """Convert a GeoJSON feature into a flat tabular record."""
    properties = feature.get("properties", {})
    geometry = feature.get("geometry", {})
    coordinates = geometry.get("coordinates", [])

    record = flatten_dict(properties)
    record["longitude"] = coordinates[0] if len(coordinates) > 0 else None
    record["latitude"] = coordinates[1] if len(coordinates) > 1 else None
    return record


def flatten_dict(data: dict, parent_key: str = "") -> dict:
    """Flatten nested address properties while preserving Chinese and English prefixes."""
    items: list[tuple[str, object]] = []
    for key, value in data.items():
        prefix = ""
        if "ChiPremisesAddress" in parent_key or "ChiVillage" in parent_key:
            prefix = "ch_"
        elif "EngPremisesAddress" in parent_key or "EngVillage" in parent_key:
            prefix = "en_"

        new_key = f"{prefix}{key}" if prefix else key

        if isinstance(value, dict):
            items.extend(flatten_dict(value, new_key).items())
        else:
            items.append((new_key, value))

    return dict(items)
