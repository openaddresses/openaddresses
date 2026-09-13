#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Sanity-check real batch job output for an OpenAddresses source.

Downloads the actual GeoJSON produced by batch.openaddresses.io for a job (or
set of jobs) and reports field population rates, sample values, and automated
flags for known bug patterns (unstripped ESRI ".0" suffixes, unanchored-regexp
leaks, duplicated street-type words, suspiciously-constant fields, etc). This
replaces doing the same thing by hand with curl + gunzip + ad-hoc python.

Compact, human/LLM-readable plain text output (not JSON).

Usage:
  uv run .claude/bin/oa-verify-output.py <job_id>
  uv run .claude/bin/oa-verify-output.py <source_path>
  uv run .claude/bin/oa-verify-output.py --pr <pr_number>
  uv run .claude/bin/oa-verify-output.py '#8514'

Examples:
  uv run .claude/bin/oa-verify-output.py 912317
  uv run .claude/bin/oa-verify-output.py us/tx/city_of_amarillo
  uv run .claude/bin/oa-verify-output.py --pr 8514
  uv run .claude/bin/oa-verify-output.py --sample-size 2000 us/ca/alameda
"""

import argparse
import gzip
import io
import json
import random
import re
import subprocess
import sys
import urllib.error
import urllib.request

API_BASE = "https://batch.openaddresses.io/api"
USER_AGENT = "oa-verify-output/1.0 (+openaddresses/addresses tooling)"

# A bare numeric-with-decorations string that looks like a PR reference:
# "#8514", "pr8514", "pr:8514", "pr-8514", "PR 8514", etc.
PR_PATTERN = re.compile(r"^(?:#|pr[:\-_ ]?)(\d+)$", re.IGNORECASE)

DEFAULT_SAMPLE_SIZE = 5000
DEFAULT_HISTORY = 100

# Known content fields per layer type (from schema/layers/*_conform.json),
# excluding structural/geometry keys. "hash" is always present but is a
# content hash, not a conformed value, so it's never reported on.
LAYER_FIELDS = {
    "addresses": ["number", "street", "unit", "city", "district", "region", "postcode", "id", "accuracy"],
    "parcels": ["pid"],
    "buildings": ["height", "levels", "id"],
    "centerlines": [
        "name", "oneway", "speed", "classification", "surface",
        "addr_from_left", "addr_to_left", "addr_from_right", "addr_to_right",
        "zip_left", "zip_right", "id",
    ],
}
ALWAYS_IGNORE_FIELDS = {"hash"}

# Fields where a single distinct value across a big sample is unremarkable
# enough that flagging it is more noise than signal.
CONSTANT_OK_FIELDS = {"accuracy"}


def api_get(path):
    """GET a JSON endpoint from the batch API."""
    url = f"{API_BASE}{path}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        print(f"ERROR: HTTP {e.code} fetching {url}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"ERROR: {e.reason} fetching {url}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"ERROR: {e} fetching {url}", file=sys.stderr)
        return None


def get_job_detail(job_id):
    """Fetch full detail for a single job id."""
    return api_get(f"/job/{job_id}")


def get_latest_jobs_for_source(source_path, history=DEFAULT_HISTORY):
    """Return the most recent job summary per (layer, name) group for a source path."""
    data = api_get(f"/job?source={source_path}&order=desc&limit={history}")
    if not data:
        return []
    jobs = data.get("jobs", [])
    if not jobs:
        return []
    groups = {}
    for j in jobs:
        key = (j.get("layer"), j.get("name"))
        # Jobs come back newest-first, so the first one seen per group wins.
        if key not in groups:
            groups[key] = j
    return list(groups.values())


def source_paths_from_pr(pr_number):
    """Use `gh pr diff --name-only` to find changed sources/**/*.json files
    and map each to its <country>/<state>/<coverage> source path.
    """
    try:
        result = subprocess.run(
            ["gh", "pr", "diff", str(pr_number), "--name-only"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except FileNotFoundError:
        print("ERROR: `gh` CLI not found. Install/authenticate GitHub CLI to use --pr.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"ERROR: failed to run `gh pr diff`: {e}", file=sys.stderr)
        return []

    if result.returncode != 0:
        print(f"ERROR: `gh pr diff {pr_number} --name-only` failed: {result.stderr.strip()}", file=sys.stderr)
        return []

    paths = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if line.startswith("sources/") and line.endswith(".json"):
            # sources/us/id/canyon.json -> us/id/canyon
            source_path = line[len("sources/"):-len(".json")]
            paths.append(source_path)

    if not paths:
        print(f"No changed sources/**/*.json files found in PR #{pr_number}.", file=sys.stderr)
    return paths


def resolve_url(job_detail):
    """Pick the best available output URL for a job, preferring validated output.

    s3:// URIs are converted to https:// since the bucket is served directly
    over HTTPS at the same path.
    """
    for key in ("s3_validated", "s3"):
        uri = job_detail.get(key)
        if uri:
            if uri.startswith("s3://"):
                return "https://" + uri[len("s3://"):]
            return uri
    # Defensive fallback in case the API nests these under "output" instead.
    output = job_detail.get("output") or {}
    for key in ("s3_validated", "s3"):
        uri = output.get(key)
        if uri:
            if uri.startswith("s3://"):
                return "https://" + uri[len("s3://"):]
            return uri
    return None


def stream_sample_features(url, sample_size):
    """Stream-download and gunzip a job's output, reservoir-sampling up to
    sample_size features without holding the whole file in memory.

    Returns (sample, total_count, parse_errors) or raises on network failure.
    """
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    sample = []
    total_count = 0
    parse_errors = 0

    with urllib.request.urlopen(req, timeout=60) as resp:
        with gzip.GzipFile(fileobj=resp) as gz:
            text = io.TextIOWrapper(gz, encoding="utf-8", errors="replace")
            for line in text:
                line = line.strip()
                if not line:
                    continue
                total_count += 1
                try:
                    feature = json.loads(line)
                except json.JSONDecodeError:
                    parse_errors += 1
                    continue
                if len(sample) < sample_size:
                    sample.append(feature)
                else:
                    j = random.randint(0, total_count - 1)
                    if j < sample_size:
                        sample[j] = feature

    return sample, total_count, parse_errors


def is_empty(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


TRAILING_DOT_ZERO = re.compile(r"^\d+\.0$")
LEAKED_NUMERIC_PREFIX = re.compile(r"^\d+\s+\D")


def check_trailing_dot_zero(field, values):
    bad = [v for v in values if isinstance(v, str) and TRAILING_DOT_ZERO.match(v)]
    if bad:
        examples = ", ".join(repr(v) for v in bad[:5])
        return f'trailing ".0" artifact on {len(bad)} sampled value(s) (ESRI Double field not stripped) e.g. {examples}'
    return None


def check_leaked_numeric_prefix(field, values):
    bad = [v for v in values if isinstance(v, str) and LEAKED_NUMERIC_PREFIX.match(v)]
    if bad:
        examples = ", ".join(repr(v) for v in bad[:5])
        return (
            f"possible unanchored regexp leak: {len(bad)} sampled value(s) start with a digit run "
            f"then text (not necessarily wrong, but worth eyeballing) e.g. {examples}"
        )
    return None


def check_duplicated_trailing_word(field, values):
    bad = []
    for v in values:
        if not isinstance(v, str):
            continue
        tokens = v.split()
        if len(tokens) >= 2 and tokens[-1].lower() == tokens[-2].lower():
            bad.append(v)
    if bad:
        examples = ", ".join(repr(v) for v in bad[:5])
        return f"duplicated trailing word on {len(bad)} sampled value(s) e.g. {examples}"
    return None


# Which heuristic checks apply to which fields.
FIELD_CHECKS = {
    "number": [check_trailing_dot_zero],
    "postcode": [check_trailing_dot_zero],
    "city": [check_leaked_numeric_prefix],
    "region": [check_leaked_numeric_prefix],
    "district": [check_leaked_numeric_prefix],
    "street": [check_duplicated_trailing_word],
}


def format_pct(n, d):
    if d == 0:
        return "n/a"
    return f"{100.0 * n / d:.1f}%"


def report_job(job_detail, sample_size):
    job_id = job_detail.get("id")
    source_name = job_detail.get("source_name", "?")
    layer = job_detail.get("layer", "?")
    name = job_detail.get("name", "?")
    status = job_detail.get("status", "?")

    print("=" * 78)
    print(f"Job {job_id} | {source_name} | layer={layer} name={name} | status={status}")
    print("=" * 78)

    url = resolve_url(job_detail)
    if not url:
        print(f"  No output available for this job (status: {status}). Skipping.")
        print()
        return

    validated_used = bool(job_detail.get("s3_validated"))
    print(f"  Output: {url}{'  (validated)' if validated_used else '  (unvalidated/raw)'}")

    try:
        sample, total_count, parse_errors = stream_sample_features(url, sample_size)
    except urllib.error.HTTPError as e:
        print(f"  ERROR: HTTP {e.code} downloading output. Skipping.")
        print()
        return
    except urllib.error.URLError as e:
        print(f"  ERROR: {e.reason} downloading output. Skipping.")
        print()
        return
    except Exception as e:
        print(f"  ERROR: failed to download/parse output ({e}). Skipping.")
        print()
        return

    if total_count == 0:
        print("  Job output contains zero features.")
        print()
        return

    print(f"  Total features: {total_count}  |  Sampled: {len(sample)}"
          + (f"  |  Unparseable lines skipped: {parse_errors}" if parse_errors else ""))
    print()

    # Gather every property key actually present in the sample.
    keys_seen = set()
    for feat in sample:
        props = feat.get("properties") or {}
        keys_seen.update(props.keys())
    keys_seen -= ALWAYS_IGNORE_FIELDS

    known_for_layer = LAYER_FIELDS.get(layer)
    if known_for_layer:
        fields_to_check = [f for f in known_for_layer if f in keys_seen]
    else:
        # Unknown layer type: fall back to whatever keys are present.
        fields_to_check = sorted(keys_seen)

    if not fields_to_check:
        print("  (No attribute fields present in output — expected for buildings/geometry-only layers.)")
        print()
        return

    all_flags = []

    for field in fields_to_check:
        values = [ (feat.get("properties") or {}).get(field) for feat in sample ]
        non_empty = [v for v in values if not is_empty(v)]
        pop_rate = format_pct(len(non_empty), len(values))

        counts = {}
        for v in non_empty:
            key = str(v)
            counts[key] = counts.get(key, 0) + 1
        distinct = sorted(counts.items(), key=lambda kv: -kv[1])
        distinct_count = len(distinct)
        top_values = ", ".join(repr(v) for v, _ in distinct[:5])

        print(f"  {field:<12s} populated={pop_rate:>6s}  distinct={distinct_count:<6d}  samples: {top_values}")

        # Defect flags for this field.
        field_flags = []
        for check in FIELD_CHECKS.get(field, []):
            result = check(field, non_empty)
            if result:
                field_flags.append(result)

        if (
            len(sample) > 100
            and len(non_empty) == len(values)
            and distinct_count == 1
            and field not in CONSTANT_OK_FIELDS
        ):
            field_flags.append(
                f'check: "{field}" is 100% populated but only has one distinct value '
                f"across {len(sample)} sampled features — verify this isn't a mapping bug"
            )

        for flag in field_flags:
            all_flags.append(f"{field}: {flag}")

    print()
    if all_flags:
        print("  Flags:")
        for flag in all_flags:
            print(f"    - {flag}")
    else:
        print("  Flags: none of the known defect patterns detected.")
    print()


def classify_target(target, pr_flag):
    if pr_flag is not None:
        return ("pr", pr_flag)
    if target is None:
        return (None, None)

    target = target.strip()
    m = PR_PATTERN.match(target)
    if m:
        return ("pr", int(m.group(1)))
    if "/" in target:
        return ("source", target.strip("/"))
    if target.isdigit():
        return ("job", int(target))
    return (None, target)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "target", nargs="?",
        help="Job id (e.g. 912317), source path (e.g. us/tx/city_of_amarillo), "
             "or a PR reference (e.g. '#8514' or 'pr8514')",
    )
    parser.add_argument("--pr", type=int, default=None, help="GitHub PR number to check changed sources for")
    parser.add_argument(
        "--sample-size", type=int, default=DEFAULT_SAMPLE_SIZE,
        help=f"Max features to sample per job (default: {DEFAULT_SAMPLE_SIZE})",
    )
    parser.add_argument(
        "--history", type=int, default=DEFAULT_HISTORY,
        help=f"How many recent jobs to scan per source when looking up by source path (default: {DEFAULT_HISTORY})",
    )
    args = parser.parse_args()

    mode, value = classify_target(args.target, args.pr)

    if mode is None:
        if value is None:
            print("ERROR: provide a job id, source path, or --pr <number>.", file=sys.stderr)
        else:
            print(f"ERROR: could not classify target {value!r} as a job id, source path, or PR reference.", file=sys.stderr)
        sys.exit(1)

    job_details = []

    if mode == "job":
        detail = get_job_detail(value)
        if detail is None:
            print(f"ERROR: could not fetch job {value}.", file=sys.stderr)
            sys.exit(1)
        job_details.append(detail)

    elif mode == "source":
        summaries = get_latest_jobs_for_source(value, history=args.history)
        if not summaries:
            print(f"No jobs found for source {value!r}.")
            sys.exit(1)
        for summary in summaries:
            detail = get_job_detail(summary["id"])
            if detail is not None:
                job_details.append(detail)

    elif mode == "pr":
        source_paths = source_paths_from_pr(value)
        if not source_paths:
            sys.exit(1)
        print(f"PR #{value}: found {len(source_paths)} changed source(s): {', '.join(source_paths)}")
        print()
        for source_path in source_paths:
            summaries = get_latest_jobs_for_source(source_path, history=args.history)
            if not summaries:
                print(f"No jobs found for source {source_path!r}.")
                continue
            for summary in summaries:
                detail = get_job_detail(summary["id"])
                if detail is not None:
                    job_details.append(detail)

    if not job_details:
        print("No jobs to report on.", file=sys.stderr)
        sys.exit(1)

    for detail in job_details:
        report_job(detail, args.sample_size)


if __name__ == "__main__":
    main()
