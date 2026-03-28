#!/usr/bin/env python3
"""
Fetch Denmark address data from Datafordeler DAR GraphQL API and write a CSV.
Coordinates are in EPSG:25832.

Primary entity: DAR_Adresse (one row per door/unit address)
Lookup chain:
  DAR_Adresse
    └─ husnummer  → DAR_Husnummer
                      ├─ adgangspunkt    → DAR_Adressepunkt  (coordinates)
                      ├─ navngivenVej    → DAR_NavngivenVej  (street name)
                      ├─ postnummer      → DAR_Postnummer    (postcode + city)
                      └─ supplerendeBynavn → DAR_SupplerendeBynavn (district)

Lookup tables are cached to disk and not re-fetched on resume.
The DAR_Adresse stream is checkpointed after each page.

Sample mode (--sample N) fetches N adresse records first, then does targeted
lookups for only the referenced IDs — no full table scans.

Usage:
    export DAR_API_KEY="your_api_key"
    python countrywide.py --sample 100          # quick check → dk_sample.csv
    python countrywide.py                        # full run, resumes if interrupted
    python countrywide.py --out dk_countrywide.csv --zip
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import zipfile
from pathlib import Path

import requests

GRAPHQL_URL = "https://graphql.datafordeler.dk/DAR/v1"
TRANSIENT_CODES = {429, 500, 502, 503, 504}
FLUSH_EVERY = 10_000

CSV_COLUMNS = ["x", "y", "number", "street", "unit", "postcode", "city", "district", "region"]

# Maps 4-digit kommunekode (string) → region name.
# Source: Danmarks Statistik / 2007 municipal reform.
KOMMUNEKODE_TO_REGION = {
    # Region Hovedstaden
    "0101": "Region Hovedstaden", "0147": "Region Hovedstaden", "0151": "Region Hovedstaden",
    "0153": "Region Hovedstaden", "0155": "Region Hovedstaden", "0157": "Region Hovedstaden",
    "0159": "Region Hovedstaden", "0161": "Region Hovedstaden", "0163": "Region Hovedstaden",
    "0165": "Region Hovedstaden", "0167": "Region Hovedstaden", "0169": "Region Hovedstaden",
    "0173": "Region Hovedstaden", "0175": "Region Hovedstaden", "0183": "Region Hovedstaden",
    "0185": "Region Hovedstaden", "0187": "Region Hovedstaden", "0190": "Region Hovedstaden",
    "0201": "Region Hovedstaden", "0210": "Region Hovedstaden", "0217": "Region Hovedstaden",
    "0219": "Region Hovedstaden", "0223": "Region Hovedstaden", "0230": "Region Hovedstaden",
    "0240": "Region Hovedstaden", "0250": "Region Hovedstaden", "0260": "Region Hovedstaden",
    "0270": "Region Hovedstaden", "0400": "Region Hovedstaden", "0411": "Region Hovedstaden",
    # Region Sjælland
    "0253": "Region Sjælland", "0259": "Region Sjælland", "0265": "Region Sjælland",
    "0269": "Region Sjælland", "0306": "Region Sjælland", "0316": "Region Sjælland",
    "0320": "Region Sjælland", "0326": "Region Sjælland", "0329": "Region Sjælland",
    "0330": "Region Sjælland", "0336": "Region Sjælland", "0340": "Region Sjælland",
    "0350": "Region Sjælland", "0360": "Region Sjælland", "0370": "Region Sjælland",
    "0376": "Region Sjælland", "0390": "Region Sjælland",
    # Region Syddanmark
    "0410": "Region Syddanmark", "0420": "Region Syddanmark", "0430": "Region Syddanmark",
    "0440": "Region Syddanmark", "0450": "Region Syddanmark", "0461": "Region Syddanmark",
    "0479": "Region Syddanmark", "0480": "Region Syddanmark", "0482": "Region Syddanmark",
    "0492": "Region Syddanmark", "0510": "Region Syddanmark", "0530": "Region Syddanmark",
    "0540": "Region Syddanmark", "0550": "Region Syddanmark", "0561": "Region Syddanmark",
    "0563": "Region Syddanmark", "0573": "Region Syddanmark", "0575": "Region Syddanmark",
    "0580": "Region Syddanmark", "0607": "Region Syddanmark", "0621": "Region Syddanmark",
    "0630": "Region Syddanmark",
    # Region Midtjylland
    "0615": "Region Midtjylland", "0657": "Region Midtjylland", "0661": "Region Midtjylland",
    "0665": "Region Midtjylland", "0671": "Region Midtjylland", "0706": "Region Midtjylland",
    "0707": "Region Midtjylland", "0710": "Region Midtjylland", "0727": "Region Midtjylland",
    "0730": "Region Midtjylland", "0740": "Region Midtjylland", "0741": "Region Midtjylland",
    "0746": "Region Midtjylland", "0751": "Region Midtjylland", "0756": "Region Midtjylland",
    "0760": "Region Midtjylland", "0766": "Region Midtjylland", "0779": "Region Midtjylland",
    "0791": "Region Midtjylland",
    # Region Nordjylland
    "0773": "Region Nordjylland", "0787": "Region Nordjylland", "0810": "Region Nordjylland",
    "0813": "Region Nordjylland", "0820": "Region Nordjylland", "0825": "Region Nordjylland",
    "0840": "Region Nordjylland", "0846": "Region Nordjylland", "0849": "Region Nordjylland",
    "0851": "Region Nordjylland", "0860": "Region Nordjylland",
}

ADRESSE_FIELDS = "\n".join([
    "id_lokalId",
    "etagebetegnelse",
    "doerbetegnelse",
    "husnummer",
])

HUSNUMMER_LOOKUP_FIELDS = "\n".join([
    "id_lokalId",
    "husnummertekst",
    "adgangspunkt",
    "navngivenVej",
    "postnummer",
    "supplerendeBynavn",
])


# ---------------------------------------------------------------------------
# GraphQL helpers
# ---------------------------------------------------------------------------

def _post(api_key: str, payload: dict, retries: int, backoff: float) -> dict:
    headers = {"Content-Type": "application/json"}
    params = {"apikey": api_key}
    attempt = 0
    while True:
        try:
            r = requests.post(GRAPHQL_URL, json=payload, params=params,
                              headers=headers, timeout=120)
            if r.status_code in TRANSIENT_CODES:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as exc:
            attempt += 1
            if attempt > retries:
                raise
            wait = backoff ** attempt
            print(f"  Retry {attempt}/{retries} ({exc}), sleeping {wait:.1f}s", flush=True)
            time.sleep(wait)


def _gql_scan_query(entity: str, fields: str, page_size: int, extra_where: str = "") -> str:
    where = f"registreringTil: {{ eq: null }}"
    if extra_where:
        where += f", {extra_where}"
    return f"""
query ($virkningstid: DafDateTime!, $after: String) {{
  {entity}(
    virkningstid: $virkningstid
    where: {{ {where} }}
    first: {page_size}
    after: $after
  ) {{
    pageInfo {{ endCursor hasNextPage }}
    nodes {{ {fields} }}
  }}
}}
"""


def _gql_ids_query(entity: str, id_field: str, fields: str, page_size: int,
                   extra_where: str = "") -> str:
    where = f"{id_field}: {{ in: $ids }}, registreringTil: {{ eq: null }}"
    if extra_where:
        where += f", {extra_where}"
    return f"""
query ($virkningstid: DafDateTime!, $ids: [String!]!, $after: String) {{
  {entity}(
    virkningstid: $virkningstid
    where: {{ {where} }}
    first: {page_size}
    after: $after
  ) {{
    pageInfo {{ endCursor hasNextPage }}
    nodes {{ {fields} }}
  }}
}}
"""


def fetch_pages(
    api_key: str,
    entity: str,
    fields: str,
    virkningstid: str,
    page_size: int,
    start_cursor: str = None,
    max_records: int = 0,
    retries: int = 5,
    backoff: float = 1.5,
    extra_where: str = "",
):
    """Generator that yields (end_cursor, nodes) per page."""
    query = _gql_scan_query(entity, fields, page_size, extra_where)
    cursor = start_cursor
    page = 0
    total_yielded = 0

    while True:
        data = _post(api_key,
                     {"query": query,
                      "variables": {"virkningstid": virkningstid, "after": cursor}},
                     retries, backoff)

        if "errors" in data:
            print(f"GraphQL errors ({entity}): {data['errors']}", file=sys.stderr, flush=True)
            sys.exit(1)

        connection = data.get("data", {}).get(entity, {})
        nodes = connection.get("nodes") or []
        page_info = connection.get("pageInfo", {})
        end_cursor = page_info.get("endCursor")
        page += 1

        if max_records and total_yielded + len(nodes) >= max_records:
            nodes = nodes[: max_records - total_yielded]
            print(f"  [{entity}] Page {page}: {len(nodes)} records (sample limit)", flush=True)
            yield end_cursor, nodes
            break

        print(f"  [{entity}] Page {page}: {len(nodes)} records", flush=True)
        total_yielded += len(nodes)
        yield end_cursor, nodes

        if not page_info.get("hasNextPage"):
            break
        cursor = end_cursor


def fetch_all(api_key, entity, fields, virkningstid, page_size, retries=5, backoff=1.5):
    for _, nodes in fetch_pages(api_key, entity, fields, virkningstid, page_size,
                                retries=retries, backoff=backoff):
        yield from nodes


def fetch_by_ids(api_key, entity, id_field, fields, virkningstid, ids,
                 batch_size=100, page_size=1000, retries=5, backoff=1.5) -> list:
    """Fetch records by a list of IDs.

    Uses batches of batch_size IDs per query, with pagination inside each batch
    to handle the multiple registration-period rows the API returns per ID.
    Deduplicates by id_lokalId, keeping the last occurrence.
    """
    query = _gql_ids_query(entity, id_field, fields, page_size)
    seen: dict = {}
    unique_ids = list(dict.fromkeys(ids))
    for i in range(0, len(unique_ids), batch_size):
        batch = unique_ids[i: i + batch_size]
        cursor = None
        while True:
            data = _post(api_key,
                         {"query": query,
                          "variables": {"virkningstid": virkningstid,
                                        "ids": batch, "after": cursor}},
                         retries, backoff)
            if "errors" in data:
                print(f"GraphQL errors ({entity} by IDs): {data['errors']}",
                      file=sys.stderr, flush=True)
                sys.exit(1)
            conn = data.get("data", {}).get(entity, {})
            for node in conn.get("nodes") or []:
                lid = node.get("id_lokalId")
                if lid:
                    seen[lid] = node
            page_info = conn.get("pageInfo", {})
            if not page_info.get("hasNextPage"):
                break
            cursor = page_info.get("endCursor")
    return list(seen.values())


# ---------------------------------------------------------------------------
# Disk cache
# ---------------------------------------------------------------------------

def _cache_path(out_csv: Path, name: str) -> Path:
    return out_csv.with_name(out_csv.stem + f".{name}_cache.json")


def _load_cache(path, virkningstid: str):
    if not path or not path.exists():
        return None
    try:
        with path.open(encoding="utf-8") as f:
            wrapper = json.load(f)
        if wrapper.get("virkningstid") != virkningstid:
            print(f"  Cache {path.name} has different virkningstid; ignoring.", flush=True)
            return None
        print(f"  Loaded {len(wrapper['data'])} entries from {path.name}", flush=True)
        return wrapper["data"]
    except Exception as exc:
        print(f"  Could not read cache {path.name}: {exc}; re-fetching.", flush=True)
        return None


def _save_cache(path: Path, data: dict, virkningstid: str):
    with path.open("w", encoding="utf-8") as f:
        json.dump({"virkningstid": virkningstid, "data": data}, f, separators=(",", ":"))
    print(f"  Saved cache to {path.name}", flush=True)


# ---------------------------------------------------------------------------
# Lookup builders — full scans (with disk cache)
# ---------------------------------------------------------------------------

def build_husnummer_lookup(api_key, virkningstid, page_size, cache_path=None,
                           retries=5, backoff=1.5):
    cached = _load_cache(cache_path, virkningstid)
    if cached is not None:
        return cached
    print("Fetching DAR_Husnummer (full)...", flush=True)
    lookup = {}
    for node in fetch_all(api_key, "DAR_Husnummer", HUSNUMMER_LOOKUP_FIELDS,
                          virkningstid, page_size, retries=retries, backoff=backoff):
        if node.get("id_lokalId"):
            lookup[node["id_lokalId"]] = {
                "husnummertekst":    node.get("husnummertekst"),
                "adgangspunkt":      node.get("adgangspunkt"),
                "navngivenVej":      node.get("navngivenVej"),
                "postnummer":        node.get("postnummer"),
                "supplerendeBynavn": node.get("supplerendeBynavn"),
            }
    print(f"  DAR_Husnummer: {len(lookup)} entries", flush=True)
    if cache_path:
        _save_cache(cache_path, lookup, virkningstid)
    return lookup


def build_adressepunkt_lookup(api_key, virkningstid, page_size, cache_path=None,
                               retries=5, backoff=1.5):
    cached = _load_cache(cache_path, virkningstid)
    if cached is not None:
        return {k: tuple(v) for k, v in cached.items()}
    print("Fetching DAR_Adressepunkt (full)...", flush=True)
    lookup = {}
    for node in fetch_all(api_key, "DAR_Adressepunkt", "id_lokalId\nposition { wkt }",
                          virkningstid, page_size, retries=retries, backoff=backoff):
        wkt = (node.get("position") or {}).get("wkt")
        x, y = _parse_wkt_point(wkt)
        if node.get("id_lokalId") and x is not None:
            lookup[node["id_lokalId"]] = (x, y)
    print(f"  DAR_Adressepunkt: {len(lookup)} entries", flush=True)
    if cache_path:
        _save_cache(cache_path, {k: list(v) for k, v in lookup.items()}, virkningstid)
    return lookup


def build_vejnavn_lookup(api_key, virkningstid, page_size, cache_path=None,
                         retries=5, backoff=1.5):
    cached = _load_cache(cache_path, virkningstid)
    if cached is not None:
        return cached
    print("Fetching DAR_NavngivenVej (full)...", flush=True)
    lookup = {}
    for node in fetch_all(api_key, "DAR_NavngivenVej",
                          "id_lokalId\nvejnavn\nadministreresAfKommune",
                          virkningstid, page_size, retries=retries, backoff=backoff):
        if node.get("id_lokalId"):
            lookup[node["id_lokalId"]] = {
                "vejnavn": node.get("vejnavn"),
                "kommunekode": node.get("administreresAfKommune"),
            }
    print(f"  DAR_NavngivenVej: {len(lookup)} entries", flush=True)
    if cache_path:
        _save_cache(cache_path, lookup, virkningstid)
    return lookup


def build_postnummer_lookup(api_key, virkningstid, page_size, cache_path=None,
                             retries=5, backoff=1.5):
    cached = _load_cache(cache_path, virkningstid)
    if cached is not None:
        return cached
    print("Fetching DAR_Postnummer (full)...", flush=True)
    lookup = {}
    for node in fetch_all(api_key, "DAR_Postnummer", "id_lokalId\npostnr\nnavn",
                          virkningstid, page_size, retries=retries, backoff=backoff):
        if node.get("id_lokalId"):
            lookup[node["id_lokalId"]] = {"postnr": node.get("postnr"), "navn": node.get("navn")}
    print(f"  DAR_Postnummer: {len(lookup)} entries", flush=True)
    if cache_path:
        _save_cache(cache_path, lookup, virkningstid)
    return lookup


def build_supplerendebynavn_lookup(api_key, virkningstid, page_size, cache_path=None,
                                   retries=5, backoff=1.5):
    cached = _load_cache(cache_path, virkningstid)
    if cached is not None:
        return cached
    print("Fetching DAR_SupplerendeBynavn (full)...", flush=True)
    lookup = {}
    for node in fetch_all(api_key, "DAR_SupplerendeBynavn", "id_lokalId\nnavn",
                          virkningstid, page_size, retries=retries, backoff=backoff):
        if node.get("id_lokalId"):
            lookup[node["id_lokalId"]] = node.get("navn")
    print(f"  DAR_SupplerendeBynavn: {len(lookup)} entries", flush=True)
    if cache_path:
        _save_cache(cache_path, lookup, virkningstid)
    return lookup


# ---------------------------------------------------------------------------
# Lookup builders — targeted (sample mode)
# ---------------------------------------------------------------------------

def _targeted(api_key, virkningstid, entity, id_field, fields, ids, label,
              retries=5, backoff=1.5):
    unique = len(set(ids))
    print(f"Fetching {unique} {label} IDs (targeted)...", flush=True)
    lookup = {}
    for node in fetch_by_ids(api_key, entity, id_field, fields, virkningstid,
                              ids, retries=retries, backoff=backoff):
        if node.get("id_lokalId"):
            lookup[node["id_lokalId"]] = node
    print(f"  Resolved {len(lookup)} {label}", flush=True)
    return lookup


def build_husnummer_lookup_for_ids(api_key, virkningstid, ids, retries=5, backoff=1.5):
    raw = _targeted(api_key, virkningstid, "DAR_Husnummer", "id_lokalId",
                    HUSNUMMER_LOOKUP_FIELDS, ids, "husnumre", retries, backoff)
    return {k: {
        "husnummertekst":    v.get("husnummertekst"),
        "adgangspunkt":      v.get("adgangspunkt"),
        "navngivenVej":      v.get("navngivenVej"),
        "postnummer":        v.get("postnummer"),
        "supplerendeBynavn": v.get("supplerendeBynavn"),
    } for k, v in raw.items()}


def build_adressepunkt_lookup_for_ids(api_key, virkningstid, ids, retries=5, backoff=1.5):
    print(f"Fetching {len(set(ids))} adressepunkt IDs (targeted)...", flush=True)
    lookup = {}
    for node in fetch_by_ids(api_key, "DAR_Adressepunkt", "id_lokalId",
                              "id_lokalId\nposition { wkt }", virkningstid, ids,
                              retries=retries, backoff=backoff):
        wkt = (node.get("position") or {}).get("wkt")
        x, y = _parse_wkt_point(wkt)
        if node.get("id_lokalId") and x is not None:
            lookup[node["id_lokalId"]] = (x, y)
    print(f"  Resolved {len(lookup)} adressepunkter", flush=True)
    return lookup


def build_vejnavn_lookup_for_ids(api_key, virkningstid, ids, retries=5, backoff=1.5):
    raw = _targeted(api_key, virkningstid, "DAR_NavngivenVej", "id_lokalId",
                    "id_lokalId\nvejnavn\nadministreresAfKommune", ids, "vejnavne", retries, backoff)
    return {k: {
        "vejnavn": v.get("vejnavn"),
        "kommunekode": v.get("administreresAfKommune"),
    } for k, v in raw.items()}


def build_postnummer_lookup_for_ids(api_key, virkningstid, ids, retries=5, backoff=1.5):
    raw = _targeted(api_key, virkningstid, "DAR_Postnummer", "id_lokalId",
                    "id_lokalId\npostnr\nnavn", ids, "postnumre", retries, backoff)
    return {k: {"postnr": v.get("postnr"), "navn": v.get("navn")} for k, v in raw.items()}


def build_supplerendebynavn_lookup_for_ids(api_key, virkningstid, ids, retries=5, backoff=1.5):
    raw = _targeted(api_key, virkningstid, "DAR_SupplerendeBynavn", "id_lokalId",
                    "id_lokalId\nnavn", ids, "supplerendeBynavn", retries, backoff)
    return {k: v.get("navn") for k, v in raw.items()}


# ---------------------------------------------------------------------------
# Checkpoint
# ---------------------------------------------------------------------------

def _checkpoint_path(out_csv: Path) -> Path:
    return out_csv.with_name(out_csv.stem + ".checkpoint.json")


def load_checkpoint(path: Path, virkningstid: str):
    if not path.exists():
        return None, 0
    try:
        with path.open(encoding="utf-8") as f:
            cp = json.load(f)
        if cp.get("virkningstid") != virkningstid:
            print("Checkpoint virkningstid mismatch; starting fresh.", flush=True)
            return None, 0
        cursor, rows = cp.get("cursor"), cp.get("rows_written", 0)
        print(f"Resuming from checkpoint: {rows} rows, cursor={cursor}", flush=True)
        return cursor, rows
    except Exception as exc:
        print(f"Could not read checkpoint: {exc}; starting fresh.", flush=True)
        return None, 0


def save_checkpoint(path: Path, cursor, rows_written: int, virkningstid: str):
    with path.open("w", encoding="utf-8") as f:
        json.dump({"cursor": cursor, "rows_written": rows_written,
                   "virkningstid": virkningstid}, f)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def _parse_wkt_point(wkt: str):
    if not wkt:
        return None, None
    m = re.match(r"POINT\s*\(\s*([^\s]+)\s+([^\s]+)\s*\)", wkt, re.IGNORECASE)
    return (float(m.group(1)), float(m.group(2))) if m else (None, None)


def _unit(etage, doer):
    parts = [p for p in (etage, doer) if p]
    return " ".join(parts) if parts else None


def _adresse_to_row(node: dict, husnumre: dict, adressepunkter: dict,
                    vejnavne: dict, postnumre: dict, supplerendebynavn: dict) -> dict:
    hn_id = node.get("husnummer")
    hn = husnumre.get(hn_id, {}) if hn_id else {}

    ap_id = hn.get("adgangspunkt")
    x, y = adressepunkter.get(ap_id, (None, None)) if ap_id else (None, None)

    vej_id = hn.get("navngivenVej")
    vej = vejnavne.get(vej_id, {}) if vej_id else {}
    post_id = hn.get("postnummer")
    post = postnumre.get(post_id, {}) if post_id else {}
    sbn_id = hn.get("supplerendeBynavn")
    kommunekode = vej.get("kommunekode") if vej else None
    region = KOMMUNEKODE_TO_REGION.get(kommunekode) if kommunekode else None

    return {
        "x": x,
        "y": y,
        "number": hn.get("husnummertekst"),
        "street": vej.get("vejnavn") if vej else None,
        "unit": _unit(node.get("etagebetegnelse"), node.get("doerbetegnelse")),
        "postcode": post.get("postnr"),
        "city": post.get("navn"),
        "district": supplerendebynavn.get(sbn_id) if sbn_id else None,
        "region": region,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Download Denmark DAR address data via GraphQL -> CSV (EPSG:25832)."
    )
    ap.add_argument("--api-key", default=os.environ.get("DAR_API_KEY", ""),
                    help="Datafordeler API key (or set DAR_API_KEY env var).")
    ap.add_argument("--out", default="dk_countrywide.csv", help="Output CSV filename.")
    ap.add_argument("--page-size", type=int, default=1000, help="Records per page (default: 1000).")
    ap.add_argument("--virkningstid", default="2026-03-26T00:00:00.000Z",
                    help="Effective time (virkningstid) for all queries (ISO 8601).")
    ap.add_argument("--retries", type=int, default=5, help="Retries on transient errors.")
    ap.add_argument("--backoff", type=float, default=1.5, help="Exponential backoff base.")
    ap.add_argument("--zip", action="store_true", help="Also write a ZIP of the CSV.")
    ap.add_argument("--sample", type=int, default=0, metavar="N",
                    help="Fetch only the first N adresse records for a quick output check.")
    args = ap.parse_args()

    if not args.api_key:
        print("Error: API key required. Set --api-key or DAR_API_KEY env var.", file=sys.stderr)
        sys.exit(1)

    sample = args.sample
    if sample and args.out == "dk_countrywide.csv":
        args.out = "dk_sample.csv"

    out_csv = Path(args.out).resolve()
    vt = args.virkningstid
    lkwargs = dict(api_key=args.api_key, virkningstid=vt,
                   retries=args.retries, backoff=args.backoff)
    fkwargs = dict(**lkwargs, page_size=args.page_size)

    if sample:
        # --- Sample mode: fetch adresse first, then targeted lookups ---
        print(f"Sample mode: fetching {sample} DAR_Adresse records...", flush=True)
        adresse_nodes = []
        seen_ids: set = set()
        for _, nodes in fetch_pages(max_records=sample, entity="DAR_Adresse",
                                    fields=ADRESSE_FIELDS,
                                    extra_where='status: { eq: "3" }', **fkwargs):
            for n in nodes:
                lid = n.get("id_lokalId")
                if lid and lid not in seen_ids:
                    seen_ids.add(lid)
                    adresse_nodes.append(n)

        hn_ids = [n["husnummer"] for n in adresse_nodes if n.get("husnummer")]
        husnumre = build_husnummer_lookup_for_ids(**lkwargs, ids=hn_ids)

        ap_ids   = [h["adgangspunkt"]      for h in husnumre.values() if h.get("adgangspunkt")]
        vej_ids  = [h["navngivenVej"]      for h in husnumre.values() if h.get("navngivenVej")]
        post_ids = [h["postnummer"]        for h in husnumre.values() if h.get("postnummer")]
        sbn_ids  = [h["supplerendeBynavn"] for h in husnumre.values() if h.get("supplerendeBynavn")]

        adressepunkter    = build_adressepunkt_lookup_for_ids(**lkwargs, ids=ap_ids)
        vejnavne          = build_vejnavn_lookup_for_ids(**lkwargs, ids=vej_ids)
        postnumre         = build_postnummer_lookup_for_ids(**lkwargs, ids=post_ids)
        supplerendebynavn = build_supplerendebynavn_lookup_for_ids(**lkwargs, ids=sbn_ids)

        with out_csv.open("w", encoding="utf-8", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            for node in adresse_nodes:
                writer.writerow(_adresse_to_row(node, husnumre, adressepunkter,
                                                vejnavne, postnumre, supplerendebynavn))

        print(f"Done. Wrote {len(adresse_nodes)} rows to {out_csv}", flush=True)

    else:
        # --- Full mode: build all lookup tables, then stream DAR_Adresse ---
        husnumre          = build_husnummer_lookup(
            **fkwargs, cache_path=_cache_path(out_csv, "husnummer"))
        adressepunkter    = build_adressepunkt_lookup(
            **fkwargs, cache_path=_cache_path(out_csv, "adressepunkt"))
        vejnavne          = build_vejnavn_lookup(
            **fkwargs, cache_path=_cache_path(out_csv, "vejnavn"))
        postnumre         = build_postnummer_lookup(
            **fkwargs, cache_path=_cache_path(out_csv, "postnummer"))
        supplerendebynavn = build_supplerendebynavn_lookup(
            **fkwargs, cache_path=_cache_path(out_csv, "supplerendebynavn"))

        cp_path = _checkpoint_path(out_csv)
        start_cursor, total = load_checkpoint(cp_path, vt)
        resuming = start_cursor is not None or (total > 0 and out_csv.exists())

        print(f"{'Resuming' if resuming else 'Starting'} DAR_Adresse stream -> {out_csv}",
              flush=True)

        with out_csv.open("a" if resuming else "w", encoding="utf-8", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=CSV_COLUMNS)
            if not resuming:
                writer.writeheader()

            seen_ids: set = set()
            for end_cursor, nodes in fetch_pages(
                start_cursor=start_cursor, entity="DAR_Adresse",
                fields=ADRESSE_FIELDS,
                extra_where='status: { eq: "3" }', **fkwargs,
            ):
                for node in nodes:
                    lid = node.get("id_lokalId")
                    if not lid or lid in seen_ids:
                        continue
                    seen_ids.add(lid)
                    writer.writerow(_adresse_to_row(node, husnumre, adressepunkter,
                                                    vejnavne, postnumre, supplerendebynavn))
                    total += 1

                fout.flush()
                save_checkpoint(cp_path, end_cursor, total, vt)
                if total % FLUSH_EVERY < args.page_size:
                    print(f"  {total} rows written", flush=True)

        print(f"Done. Wrote {total} rows to {out_csv}", flush=True)
        cp_path.unlink(missing_ok=True)
        for name in ("husnummer", "adressepunkt", "vejnavn", "postnummer", "supplerendebynavn"):
            _cache_path(out_csv, name).unlink(missing_ok=True)
        print("Cleaned up checkpoint and cache files.", flush=True)

    if args.zip:
        zip_path = str(out_csv) + ".zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            zf.write(out_csv, arcname=out_csv.name)
        print(f"Compressed to {zip_path}", flush=True)
        out_csv.unlink()


if __name__ == "__main__":
    main()
