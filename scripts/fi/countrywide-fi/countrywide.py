#!/usr/bin/env python3
import argparse
import concurrent.futures as cf
import csv
import json
import math
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Dict, Any, List, Tuple, Set

import requests

BASE_ITEMS_URL = (
    "https://paikkatiedot.ymparisto.fi/geoserver/ryhti_building/ogc/features/v1/"
    "collections/open_address/items"
)

TRANSIENT_CODES = {429, 500, 502, 503, 504}


def get_number_matched(base_url: str, timeout: int = 60) -> int:
    """Query JSON once to read numberMatched; returns -1 if absent."""
    params = {"f": "application/json", "limit": 1, "startIndex": 0}
    r = requests.get(
        base_url,
        params=params,
        timeout=timeout,
        headers={"User-Agent": "OGC-CSV-Downloader/3.0"},
    )
    r.raise_for_status()
    data = r.json()
    return int(data.get("numberMatched", -1))


def fetch_page_json(
    base_url: str,
    start_index: int,
    limit: int,
    timeout: int,
    retries: int,
    backoff: float,
) -> Dict[str, Any]:
    """Fetch one GeoJSON page; new request per call (thread-safe)."""
    params = {"f": "application/geo+json", "limit": limit, "startIndex": start_index}
    attempt = 0
    while True:
        try:
            r = requests.get(
                base_url,
                params=params,
                timeout=timeout,
                headers={"User-Agent": "OGC-CSV-Downloader/3.0"},
            )
            if r.status_code in TRANSIENT_CODES:
                raise requests.HTTPError(f"HTTP {r.status_code}", response=r)
            r.raise_for_status()
            r.encoding = "utf-8"
            return r.json()
        except requests.RequestException:
            attempt += 1
            if attempt > retries:
                raise
            time.sleep(backoff**attempt)


def fetch_and_dump_page(
    tmpdir: Path,
    base_url: str,
    page_idx: int,
    start_index: int,
    limit: int,
    timeout: int,
    retries: int,
    backoff: float,
) -> Tuple[int, int, Path]:
    """
    Worker: downloads a page and writes one NDJSON line per feature:
    {"props": { ... }, "x": <lon or None>, "y": <lat or None>}
    Returns (page_idx, feature_count, temp_path).
    """
    page = fetch_page_json(base_url, start_index, limit, timeout, retries, backoff)
    feats = page.get("features", []) or []

    out_path = tmpdir / f"page_{page_idx:07d}.ndjson"
    with out_path.open("w", encoding="utf-8", newline="") as f:
        for feat in feats:
            props: Dict[str, Any] = feat.get("properties", {}) or {}
            geom = feat.get("geometry")
            x = y = None
            if geom and geom.get("type") == "Point":
                coords = geom.get("coordinates") or []
                if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                    x, y = coords[0], coords[1]
            # if not a Point, we leave x,y as None (could compute centroid if needed)
            f.write(
                json.dumps(
                    {"props": props, "x": x, "y": y},
                    ensure_ascii=False,
                    separators=(",", ":"),
                )
            )
            f.write("\n")

    return page_idx, len(feats), out_path


def collect_header_fields(ndjson_files: List[Path]) -> List[str]:
    """Scan all NDJSON files to union property keys; return a stable, deterministic header."""
    keys: Set[str] = set()
    for p in ndjson_files:
        with p.open("r", encoding="utf-8", newline="") as f:
            for line in f:
                if not line.strip():
                    continue
                obj = json.loads(line)
                props = obj.get("props", {}) or {}
                keys.update(props.keys())

    # Deterministic order: alphabetical for reproducibility
    cols = sorted(keys)
    # Ensure x,y at the end
    cols += ["x", "y"]
    return cols


def write_csv(out_csv: Path, header: List[str], ndjson_files: List[Path]) -> int:
    """Write merged CSV from NDJSON pages in order; returns number of rows written."""
    total = 0
    with out_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow(header)

        for p in ndjson_files:
            with p.open("r", encoding="utf-8", newline="") as fin:
                for line in fin:
                    if not line.strip():
                        continue
                    obj = json.loads(line)
                    props = obj.get("props", {}) or {}
                    x = obj.get("x")
                    y = obj.get("y")

                    row = []
                    for col in header:
                        if col == "x":
                            row.append(x)
                        elif col == "y":
                            row.append(y)
                        else:
                            val = props.get(col)
                            # Normalize lists/dicts to compact JSON so CSV stays clean
                            if isinstance(val, (list, dict)):
                                val = json.dumps(
                                    val, ensure_ascii=False, separators=(",", ":")
                                )
                            row.append(val)
                    writer.writerow(row)
                    total += 1
    return total


def main():
    ap = argparse.ArgumentParser(
        description="Parallel OGC API Features downloader (GeoServer) → merged CSV with x,y."
    )
    ap.add_argument(
        "-u", "--url", default=BASE_ITEMS_URL, help="Items endpoint (no query params)."
    )
    ap.add_argument(
        "-o", "--out", default="open_address.csv", help="Output CSV filename."
    )
    ap.add_argument(
        "-l", "--limit", type=int, default=5000, help="Page size (default: 5000)."
    )
    ap.add_argument(
        "--workers", type=int, default=8, help="Concurrent page downloads (default: 8)."
    )
    ap.add_argument(
        "--timeout", type=int, default=120, help="HTTP timeout seconds (default: 120)."
    )
    ap.add_argument(
        "--retries",
        type=int,
        default=5,
        help="Retries per page on transient errors (default: 5).",
    )
    ap.add_argument(
        "--backoff",
        type=float,
        default=1.5,
        help="Exponential backoff base (default: 1.5).",
    )
    ap.add_argument(
        "--zip", action="store_true", help="Also write a ZIP of the resulting CSV."
    )
    args = ap.parse_args()

    out_csv = Path(args.out).resolve()

    try:
        number_matched = get_number_matched(args.url, timeout=args.timeout)
        if number_matched < 0:
            print(
                "⚠️  Server did not report numberMatched; cannot pre-compute pages for parallel mode.",
                file=sys.stderr,
            )
            print(
                "    Suggest re-running with a URL that reports numberMatched or switch to sequential mode.",
                file=sys.stderr,
            )
            sys.exit(2)

        page_count = math.ceil(number_matched / args.limit)
        print(
            f"numberMatched: {number_matched}  |  pages: {page_count}  |  limit: {args.limit}"
        )

        with tempfile.TemporaryDirectory(prefix="ogc_csv_") as tdir:
            tmpdir = Path(tdir)

            # Schedule workers
            jobs = []
            with cf.ThreadPoolExecutor(max_workers=args.workers) as ex:
                for page_idx in range(page_count):
                    start_index = page_idx * args.limit
                    jobs.append(
                        ex.submit(
                            fetch_and_dump_page,
                            tmpdir,
                            args.url,
                            page_idx,
                            start_index,
                            args.limit,
                            args.timeout,
                            args.retries,
                            args.backoff,
                        )
                    )
                # Gather
                results: List[Tuple[int, int, Path]] = [
                    j.result() for j in cf.as_completed(jobs)
                ]

            # Order pages
            results.sort(key=lambda t: t[0])
            page_files = [t[2] for t in results]
            counts = [t[1] for t in results]
            print(
                f"Downloaded pages. Feature counts per page (first 5): {counts[:5]} ..."
            )

            # Build header (union of all property keys) + x,y
            header = collect_header_fields(page_files)
            print(f"Header columns: {len(header)} (including x,y)")

            # Write CSV
            total = write_csv(out_csv, header, page_files)
            print(f"✅ Done (parallel). Wrote {total} rows to {out_csv}")

            if args.zip:
                zip_path = str(out_csv) + ".zip"
                with zipfile.ZipFile(
                    zip_path, "w", compression=zipfile.ZIP_DEFLATED
                ) as zf:
                    zf.write(out_csv, arcname=out_csv.name)
                print(f"📦 Compressed CSV to {zip_path}")

    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
