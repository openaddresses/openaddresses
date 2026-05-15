#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "requests",
# ]
# ///
"""Explore ArcGIS REST API servers efficiently.

Compact output optimized for LLM token consumption.

Usage:
  uv run scripts/esri-explore.py services <server_url>
  uv run scripts/esri-explore.py layers <service_url>
  uv run scripts/esri-explore.py fields <layer_url>
  uv run scripts/esri-explore.py sample <layer_url> [--count N]
  uv run scripts/esri-explore.py count <layer_url>
  uv run scripts/esri-explore.py suggest <layer_url>
  uv run scripts/esri-explore.py search <server_url> <keyword>
  uv run scripts/esri-explore.py values <layer_url> <field> [--limit N]
"""

import argparse
import json
import sys

import requests


def fetch_json(url, timeout=15):
    """Fetch JSON from an ArcGIS REST endpoint."""
    try:
        resp = requests.get(url, params={"f": "json"}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.Timeout:
        print(f"ERROR: Timeout connecting to {url}", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        print(f"ERROR: Cannot connect to {url}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_services(args):
    """List all services on a server, recursing into folders."""
    def list_services(url, prefix=""):
        data = fetch_json(url)
        if "error" in data:
            print(f"ERROR: {data['error'].get('message', data['error'])}")
            return

        for svc in data.get("services", []):
            name = svc["name"]
            stype = svc["type"]
            print(f"  {name} ({stype})")

        for folder in data.get("folders", []):
            print(f"  [{folder}/]")
            list_services(f"{url}/{folder}", prefix=f"{folder}/")

    print(f"Server: {args.url}")
    list_services(args.url)


def cmd_layers(args):
    """List layers in a MapServer or FeatureServer."""
    data = fetch_json(args.url)
    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    svc_name = data.get("documentInfo", {}).get("Title", "") or data.get("serviceDescription", "")[:60]
    if svc_name:
        print(f"Service: {svc_name}")

    for layer in data.get("layers", []):
        geom = layer.get("geometryType", "?")
        if geom:
            geom = geom.replace("esriGeometry", "")
        print(f"  {layer['id']:3d}  {layer['name']:<50s}  {geom}")

    for table in data.get("tables", []):
        print(f"  {table['id']:3d}  {table['name']:<50s}  (table)")


def cmd_fields(args):
    """Show fields for a specific layer."""
    data = fetch_json(args.url)
    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    name = data.get("name", "?")
    geom = (data.get("geometryType") or "?").replace("esriGeometry", "")
    count = data.get("maxRecordCount", "?")
    print(f"Layer: {name} | Geometry: {geom} | MaxRecords: {count}")
    print()

    for field in data.get("fields", []):
        fname = field["name"]
        falias = field.get("alias", "")
        ftype = (field.get("type") or "?").replace("esriFieldType", "")
        alias_str = f" ({falias})" if falias and falias != fname else ""
        print(f"  {fname:<30s}  {ftype:<15s}{alias_str}")


def cmd_sample(args):
    """Fetch a small sample of features."""
    count = args.count or 3

    try:
        resp = requests.get(
            f"{args.url}/query",
            params={
                "where": "1=1",
                "outFields": "*",
                "resultRecordCount": count,
                "returnGeometry": "false",
                "f": "json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    features = data.get("features", [])
    if not features:
        print("No features returned")
        return

    for i, feat in enumerate(features):
        attrs = feat.get("attributes", {})
        # Filter out null values for compactness
        attrs = {k: v for k, v in attrs.items() if v is not None and v != ""}
        print(json.dumps(attrs, separators=(",", ":")))


def cmd_search(args):
    """Search services and layers by keyword."""
    keyword = args.keyword.lower()

    def search_server(url):
        data = fetch_json(url)
        if "error" in data:
            return

        for svc in data.get("services", []):
            name = svc["name"]
            stype = svc["type"]
            if keyword in name.lower():
                print(f"  SERVICE: {name} ({stype})")
                # Also list layers in matching services
                svc_url = f"{args.url}/{name}/{stype}"
                try:
                    svc_data = fetch_json(svc_url)
                    for layer in svc_data.get("layers", []):
                        geom = (layer.get("geometryType") or "?").replace("esriGeometry", "")
                        print(f"    {layer['id']:3d}  {layer['name']:<50s}  {geom}")
                except Exception:
                    pass
            else:
                # Check layers inside non-matching services
                svc_url = f"{args.url}/{name}/{stype}"
                try:
                    svc_data = fetch_json(svc_url)
                    matching = [l for l in svc_data.get("layers", []) if keyword in l["name"].lower()]
                    if matching:
                        print(f"  SERVICE: {name} ({stype})")
                        for layer in matching:
                            geom = (layer.get("geometryType") or "?").replace("esriGeometry", "")
                            print(f"    {layer['id']:3d}  {layer['name']:<50s}  {geom}")
                except Exception:
                    pass

        for folder in data.get("folders", []):
            if keyword in folder.lower():
                print(f"  FOLDER: {folder}/")
            search_server(f"{url}/{folder}")

    print(f"Searching for '{keyword}' on {args.url}")
    search_server(args.url)


def cmd_count(args):
    """Get the total feature count for a layer."""
    try:
        resp = requests.get(
            f"{args.url}/query",
            params={
                "where": "1=1",
                "returnCountOnly": "true",
                "f": "json",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    print(f"Count: {data.get('count', '?')}")


# Patterns for detecting address-relevant fields.
# Each pattern is matched as a complete field name (case-insensitive) or with
# common prefixes like SITE_, PROP_, ADDR_, SIT_ stripped first.
FIELD_PATTERNS = {
    "number": ["house_number", "house_num", "housenum", "housenumber", "addr_num",
               "addrnum", "address_number", "str_num", "stnum", "stnbr",
               "add_number", "stno", "houseno", "nbr", "addnum", "hnbr",
               "streetnum", "street_number", "bldgno", "hse_nbr", "hno",
               "anumber"],
    "street": ["streetname", "street_name", "str_name", "stname",
               "fullstreet", "road_name", "roadname", "street", "st_name"],
    "unit": ["unit", "apt", "suite", "unit_number", "unitnumber",
             "apt_num", "aptnum", "unit_num", "propapt", "apt_no"],
    "city": ["city", "municipality", "community", "citytown",
             "propcity", "city_name", "muni_name", "place_name"],
    "postcode": ["zip", "zipcode", "zip_code", "postal", "postalcode", "postcode",
                 "propzip", "zip5"],
    "direction": ["predir", "direction", "prefix_dir", "str_dir", "st_dir",
                  "pre_dir", "sufdir", "suf_dir"],
    "suffix": ["suftype", "street_type", "sttype", "mode", "suffix",
               "st_type", "str_type", "suf_type"],
}

# Prefixes to strip when matching field names
FIELD_PREFIXES = ["site_", "prop_", "addr_", "sit_", "add_", "str_", "mail_"]


def cmd_suggest(args):
    """Analyze a layer and suggest an OpenAddresses conform mapping."""
    data = fetch_json(args.url)
    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    fields = data.get("fields", [])
    if not fields:
        print("No fields found")
        return

    field_names_lower = {f["name"].lower(): f["name"] for f in fields}

    def strip_prefix(name):
        """Strip common address field prefixes."""
        for prefix in FIELD_PREFIXES:
            if name.startswith(prefix):
                return name[len(prefix):]
        return name

    # Try to match fields to conform roles using exact match on stripped names
    matches = {}
    for role, patterns in FIELD_PATTERNS.items():
        for fname_lower, fname in field_names_lower.items():
            stripped = strip_prefix(fname_lower)
            if stripped in patterns or fname_lower in patterns:
                if role not in matches:
                    matches[role] = []
                if fname not in matches[role]:
                    matches[role].append(fname)

    # Prefer SITE_ fields over MAIL_ fields when both exist
    for role in matches:
        site_fields = [f for f in matches[role] if f.upper().startswith("SITE_")]
        if site_fields:
            matches[role] = site_fields

    # Build suggested conform
    conform = {"format": "geojson"}

    # Number field
    if "number" in matches:
        conform["number"] = matches["number"][0]
    else:
        print("WARNING: No house number field detected")

    # Street - check if we have components or a single field
    street_parts = []
    if "direction" in matches:
        street_parts.append(matches["direction"][0])
    if "street" in matches:
        street_parts.append(matches["street"][0])
    if "suffix" in matches:
        street_parts.append(matches["suffix"][0])

    if len(street_parts) > 1:
        conform["street"] = street_parts
    elif street_parts:
        conform["street"] = street_parts[0]
    else:
        print("WARNING: No street field detected")

    # Prefer unit_number over unit_prefix
    if "unit" in matches:
        num_fields = [f for f in matches["unit"] if "number" in f.lower() or "num" in f.lower()]
        conform["unit"] = num_fields[0] if num_fields else matches["unit"][0]
    if "city" in matches:
        conform["city"] = matches["city"][0]
    if "postcode" in matches:
        conform["postcode"] = matches["postcode"][0]

    geom = (data.get("geometryType") or "?").replace("esriGeometry", "")
    name = data.get("name", "?")
    print(f"Layer: {name} | Geometry: {geom}")
    print()

    # Show all fields for context
    print("Fields:")
    for f in fields:
        fname = f["name"]
        ftype = (f.get("type") or "?").replace("esriFieldType", "")
        marker = ""
        for role, matched in matches.items():
            if fname in matched:
                marker = f"  <-- {role}"
                break
        print(f"  {fname:<30s}  {ftype:<15s}{marker}")

    print()
    print("Suggested conform:")
    print(json.dumps(conform, indent=4))

    # Also get count
    try:
        resp = requests.get(
            f"{args.url}/query",
            params={"where": "1=1", "returnCountOnly": "true", "f": "json"},
            timeout=15,
        )
        count_data = resp.json()
        print(f"\nRecord count: {count_data.get('count', '?')}")
    except Exception:
        pass


def cmd_values(args):
    """Get distinct values for a field in a layer."""
    field = args.field
    limit = args.limit or 100

    # Try returnDistinctValues first
    try:
        resp = requests.get(
            f"{args.url}/query",
            params={
                "where": "1=1",
                "outFields": field,
                "returnDistinctValues": "true",
                "returnGeometry": "false",
                "resultRecordCount": limit,
                "orderByFields": field,
                "f": "json",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    if "error" in data:
        print(f"ERROR: {data['error'].get('message', data['error'])}")
        return

    features = data.get("features", [])
    if not features:
        print("No features returned")
        return

    values = sorted(
        set(str(f["attributes"].get(field, "")) for f in features)
    )
    print(f"Distinct values for '{field}' ({len(values)} values):")
    for v in values:
        print(f"  {v}")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_services = sub.add_parser("services", help="List all services on a server")
    p_services.add_argument("url", help="ArcGIS REST services URL")

    p_layers = sub.add_parser("layers", help="List layers in a service")
    p_layers.add_argument("url", help="MapServer or FeatureServer URL")

    p_fields = sub.add_parser("fields", help="Show fields for a layer")
    p_fields.add_argument("url", help="Layer URL (e.g. .../MapServer/0)")

    p_sample = sub.add_parser("sample", help="Fetch sample features")
    p_sample.add_argument("url", help="Layer URL")
    p_sample.add_argument("--count", type=int, default=3, help="Number of features (default: 3)")

    p_search = sub.add_parser("search", help="Search services by keyword")
    p_search.add_argument("url", help="ArcGIS REST services URL")
    p_search.add_argument("keyword", help="Search keyword")

    p_count = sub.add_parser("count", help="Get feature count for a layer")
    p_count.add_argument("url", help="Layer URL")

    p_suggest = sub.add_parser("suggest", help="Suggest OpenAddresses conform mapping")
    p_suggest.add_argument("url", help="Layer URL")

    p_values = sub.add_parser("values", help="Get distinct values for a field")
    p_values.add_argument("url", help="Layer URL")
    p_values.add_argument("field", help="Field name")
    p_values.add_argument("--limit", type=int, default=100, help="Max values (default: 100)")

    args = parser.parse_args()

    commands = {
        "services": cmd_services,
        "layers": cmd_layers,
        "fields": cmd_fields,
        "sample": cmd_sample,
        "search": cmd_search,
        "count": cmd_count,
        "suggest": cmd_suggest,
        "values": cmd_values,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
