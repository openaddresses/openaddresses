from __future__ import annotations

from pathlib import Path

from lib.fs import load_json_file

LANGUAGE_PREFIXES = {
    "zh": "Chi",
    "en": "Eng",
}

LANGUAGE_NEUTRAL_KEYS = {"BuildingNoFrom", "BuildingNoTo"}


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
    record["StreetNumber"] = build_street_number(record)
    record["Longitude"] = coordinates[0] if len(coordinates) > 0 else None
    record["Latitude"] = coordinates[1] if len(coordinates) > 1 else None
    return record


def build_street_number(record: dict) -> str | None:
    """Build a single street number field from flattened building number values."""
    building_no_from = record.get("BuildingNoFrom")
    building_no_to = record.get("BuildingNoTo")

    if building_no_from and building_no_to:
        return f"{building_no_from}-{building_no_to}"

    return building_no_from or None


def normalize_flattened_key(key: str, language_prefix: str) -> tuple[str, str]:
    """Normalize a key and track the active language prefix for nested address fields."""
    for prefix, language_marker in LANGUAGE_PREFIXES.items():
        if key == f"{language_marker}PremisesAddress" or key == f"{language_marker}Village":
            return "", prefix

    if key in LANGUAGE_NEUTRAL_KEYS:
        return key, ""

    language_marker = LANGUAGE_PREFIXES.get(language_prefix)
    if language_marker:
        return key.removeprefix(language_marker), language_prefix

    return key, language_prefix


def flatten_dict(data: dict, language_prefix: str = "") -> dict:
    """Flatten nested address properties with normalized language-specific keys."""
    items: list[tuple[str, object]] = []
    for key, value in data.items():
        normalized_key, next_language_prefix = normalize_flattened_key(key, language_prefix)
        new_key = (
            f"{next_language_prefix}_{normalized_key}"
            if next_language_prefix and normalized_key
            else normalized_key
        )

        if isinstance(value, dict):
            items.extend(flatten_dict(value, next_language_prefix).items())
        else:
            items.append((new_key, value))

    return dict(items)
