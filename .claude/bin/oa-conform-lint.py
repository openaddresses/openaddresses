#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.10"
# ///
"""Statically lint OpenAddresses source `conform` blocks for known bug classes.

This is a pure static text/JSON linter: it never downloads data or hits a
network endpoint. It exists to catch a handful of conform-authoring mistakes
that keep recurring across sources/*.json, purely from the JSON text itself,
so they don't have to be rediscovered one at a time by manually sampling
production job output.

Rules implemented:

  1. Unanchored `regexp` + `replace` used as a disguised full-value
     extraction (a capture-group backreference like "$1" in `replace`, but
     the `pattern` doesn't effectively anchor both ends of the string). The
     `regexp` function with `replace` does a Python-style in-place
     substring replace, not a clean full-string extraction, unless the
     match is forced to span the whole value. A pattern like
     "CITY OF (.+)$" (no anchor on the left) applied via replace "$1" to
     "675 CITY OF CALDWELL" produces "675 CALDWELL" -- the unmatched "675 "
     prefix leaks through untouched -- instead of the intended "CALDWELL".
     [BUG] severity. A `regexp` used WITHOUT `replace` (pure capture-group
     extraction, where only the captured groups are returned regardless of
     what surrounds them) is far more forgiving, so it's only flagged
     [WARN] and only when it has no anchoring at either end.

  2. ESRI number/postcode fields at risk of a leaked ".0" suffix. ESRI
     `esriFieldTypeDouble` fields serialize as e.g. "78209.0" in
     production. We can't know a field's real ESRI type without hitting
     the network, so this is a heuristic [WARN]. A first pass that fires on
     every bare `conform.number`/`conform.postcode` field name on a
     `protocol: ESRI` layer turned out to match roughly a third of every
     ESRI source in the repo (field names like "zip"/"ZipCode" are simply
     how most sources spell these) -- far too noisy to be worth skimming.
     To cut that down to something worth reading, this is additionally
     gated on corpus rarity: it only fires when the exact field name (case
     insensitive) is used for that same attribute by very few *other*
     sources anywhere in sources/**/*.json. The reasoning: OpenAddresses
     rebuilds weekly and has for years, so a field-naming convention shared
     by dozens/hundreds of sources (zip, zipcode, post_code, ...) would
     very likely have already surfaced and been fixed if it commonly
     produced ".0"-suffixed garbage; a field name that's unique or nearly
     unique in the corpus is comparatively unreviewed territory and worth
     a quick check, e.g. with esri-explore.py fields <url>. This is a
     proxy for "reviewed by many other sources," not for the field's
     actual ESRI type, so false positives (and the rare false negative)
     are still expected -- treat it as a nudge, not a verdict.

  3. Broken `chain` linkage. Per ATTRIBUTE_FUNCTIONS.md, steps after the
     first in a `chain` must reference the prior step's output via
     `oa:<variable>` (or `oa:<attribute-name>` if `variable` is omitted).
     A chain with 2+ steps where no step after the first references that
     `oa:`-prefixed name anywhere suggests the steps were never actually
     wired together -- often because the author forgot the `oa:` prefix
     and just reused the raw source field name again. [BUG] severity.

  4. NOT IMPLEMENTED (by design): duplicate-looking field lists in
     `street`/name-composition arrays (e.g. ["StreetName", "StreetType"]
     where StreetName might already embed the type). This can't be
     detected from the source JSON alone -- it requires sampling real
     data values. See the sibling script oa-verify-output.py, which
     samples actual output for this kind of check.

  5. Coded-looking field mapped straight to city/region/district. On a
     `protocol: ESRI` layer, if `city`/`region`/`district` is a bare
     field-name string whose name looks like it holds a code/id rather
     than a display string (a whole "code"/"type"/"id"/"num" segment,
     case-insensitive -- e.g. "CityCode" or "CityID", but not
     "SitusAddCity") with no `map`/`constant`/regexp cleanup, that's
     probably an uncleaned coded value. [WARN] severity, deliberately
     narrow to keep false positives rare.

Usage:
  uv run .claude/bin/oa-conform-lint.py                  # scan all of sources/**/*.json
  uv run .claude/bin/oa-conform-lint.py sources/us/ca/*.json
  uv run .claude/bin/oa-conform-lint.py path/to/one.json
  uv run .claude/bin/oa-conform-lint.py --staged          # only files staged with `git add`
  uv run .claude/bin/oa-conform-lint.py --changed         # only files that differ from master

Exit code is non-zero if any [BUG]-severity finding exists; warnings alone
exit 0. Parse errors (invalid JSON) are reported but don't affect the exit
code by themselves and don't crash the run.
"""

import argparse
import glob
import json
import re
import subprocess
import sys
from pathlib import Path

BUG = "BUG"
WARN = "WARN"
PARSE_ERROR = "PARSE_ERROR"

# Attribute keys that get the ESRI ".0"-leak heuristic (rule 2).
NUMERIC_LEAK_ATTRS = {"number", "postcode"}

# Rule 2 only fires when the field name is used by this many OTHER sources
# (i.e. corpus frequency <= this, not counting the source at hand) or fewer
# for the same attribute across the whole corpus. See rule 2 docstring above.
RARE_FIELD_THRESHOLD = 1

# Attribute keys that get the coded-field heuristic (rule 5).
NAME_ATTRS = {"city", "region", "district"}

# Whole-segment tokens (case-insensitive) that suggest a coded/id field
# rather than a human-readable name, for rule 5.
CODED_TOKENS = {"code", "type", "id", "num"}

# Keys inside a function object whose string value(s) name source fields
# (as opposed to output values, formats, etc.) -- used when checking
# whether a chain step references a prior step's `oa:` variable.
FIELD_REF_KEYS = ("field", "fields", "field_to_remove")


class Finding:
    __slots__ = ("severity", "path", "message")

    def __init__(self, severity, path, message):
        self.severity = severity
        self.path = path
        self.message = message


def effective_start_anchored(pattern):
    """True if the pattern is forced to match from the start of the string.

    A literal '^' obviously does this. So, effectively, does a pattern that
    opens with a greedy '.*'/'.+' -- since re.search always tries position 0
    first, and a leading .*/.+ can absorb any prefix, the leftmost successful
    match will start at position 0 whenever the rest of the pattern matches
    at all. Treating those as anchored avoids flagging the very common
    "$1"-strips-a-prefix idiom that's actually fine.
    """
    return bool(re.match(r"^(\^|\(?\?:?\.[*+])", pattern))


def effective_end_anchored(pattern):
    """True if the pattern is forced to match to the end of the string.

    Mirrors effective_start_anchored: a literal '$', or a trailing greedy
    '.*'/'.+' (optionally inside closing group parens), consumes to the end
    of the string so nothing trails off unmatched.
    """
    trimmed = pattern.rstrip(")")
    return trimmed.endswith("$") or bool(re.search(r"\.[*+]\??$", trimmed))


def check_regexp(value, path, findings):
    pattern = value.get("pattern")
    if not isinstance(pattern, str):
        return
    field = value.get("field", "?")
    has_replace = "replace" in value
    replace = value.get("replace", "")
    start_ok = effective_start_anchored(pattern)
    end_ok = effective_end_anchored(pattern)
    anchored = start_ok and end_ok

    if has_replace:
        has_backref = bool(re.search(r"\$\d", replace)) if isinstance(replace, str) else False
        if has_backref and not anchored:
            side = (
                "the left"
                if not start_ok and end_ok
                else "the right"
                if start_ok and not end_ok
                else "both sides"
            )
            findings.append(
                Finding(
                    BUG,
                    path,
                    f"regexp on field {field!r} has pattern {pattern!r} with replace {replace!r}, "
                    f"unanchored on {side}: this is a find/replace, not a full-string extraction, so "
                    f"any part of the value the pattern doesn't match stays in the output untouched. "
                    f"E.g. a pattern like 'CITY OF (.+)$' applied to '675 CITY OF CALDWELL' produces "
                    f"'675 CALDWELL' instead of 'CALDWELL' because the leading '675 ' never matched. "
                    f"Anchor both ends around the capture, e.g. '^.*CITY OF (.+)$'.",
                )
            )
    else:
        if not start_ok and not end_ok:
            findings.append(
                Finding(
                    WARN,
                    path,
                    f"regexp on field {field!r} with pattern {pattern!r} has no replace (only captured "
                    f"groups are returned, so this is more forgiving than a replace-based extraction), "
                    f"but it's anchored at neither end -- worth a quick check that it can't match an "
                    f"unintended substring elsewhere in the value.",
                )
            )


def collect_field_refs(step):
    """All source-field-name strings a single conform function step references."""
    refs = []
    for key in FIELD_REF_KEYS:
        val = step.get(key)
        if isinstance(val, str):
            refs.append(val)
        elif isinstance(val, list):
            refs.extend(v for v in val if isinstance(v, str))
    return refs


def check_chain(value, path, attr_name, findings):
    functions = value.get("functions")
    if not isinstance(functions, list) or len(functions) < 2:
        return
    variable = value.get("variable")
    ref_name = f"oa:{variable}" if isinstance(variable, str) and variable else f"oa:{attr_name}"

    linked = False
    for step in functions[1:]:
        if not isinstance(step, dict):
            continue
        if any(ref_name in ref for ref in collect_field_refs(step)):
            linked = True
            break

    if not linked:
        findings.append(
            Finding(
                BUG,
                path,
                f"chain has {len(functions)} steps but no step after the first references "
                f"{ref_name!r} in its field(s) -- the steps don't look like they're actually "
                f"chained together. Each step after the first must read the prior step's result "
                f"via the {ref_name!r} field name, not the raw source field again, or its output "
                f"is silently ignored.",
            )
        )


def walk_functions(value, path, attr_name, findings):
    """Recursively find regexp/chain function objects anywhere in a conform value."""
    if isinstance(value, dict):
        func = value.get("function")
        if func == "regexp":
            check_regexp(value, path, findings)
        elif func == "chain":
            check_chain(value, path, attr_name, findings)
            for i, step in enumerate(value.get("functions", []) or []):
                walk_functions(step, f"{path}.functions[{i}]", attr_name, findings)
        else:
            # Other function kinds (join/first_non_empty/format/map/etc.) only
            # hold plain field-name strings/lists, not nested function objects,
            # per schema/util/functions/*.json -- nothing further to recurse into.
            pass
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk_functions(item, f"{path}[{i}]", attr_name, findings)


def looks_coded(field_name):
    """Rule 5 heuristic: does this field name look like a code/id, not a display value?"""
    tokens = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", field_name)
    return any(t.lower() in CODED_TOKENS for t in tokens)


def lint_conform(conform, layer_type, layer_index, protocol, findings, field_freq):
    if not isinstance(conform, dict):
        return
    for attr_name, attr_value in conform.items():
        path = f"layers.{layer_type}[{layer_index}].conform.{attr_name}"

        if protocol == "ESRI" and isinstance(attr_value, str):
            if attr_name in NUMERIC_LEAK_ATTRS:
                freq = field_freq.get(attr_name, {}).get(attr_value.lower(), 0)
                # freq includes this source itself, so "other sources" is freq - 1.
                if freq - 1 <= RARE_FIELD_THRESHOLD:
                    findings.append(
                        Finding(
                            WARN,
                            path,
                            f"ESRI field {attr_value!r} used directly for {attr_name!r} with no "
                            f"'.0'-stripping step, and this field name is used by only "
                            f"{max(freq - 1, 0)} other source(s) in the corpus for {attr_name!r} "
                            f"(uncommon enough to be unreviewed territory). If this is an "
                            f"esriFieldTypeDouble field on the server, production output may "
                            f"render values like '78209.0'. Worth checking the field type (e.g. "
                            f"esri-explore.py fields <url>) and, if needed, wrapping in a regexp "
                            f"that strips a trailing '.0'.",
                        )
                    )
            elif attr_name in NAME_ATTRS and looks_coded(attr_value):
                findings.append(
                    Finding(
                        WARN,
                        path,
                        f"ESRI field {attr_value!r} mapped directly to {attr_name!r} with no "
                        f"map/constant/regexp cleanup, but the field name looks like it may hold "
                        f"a coded/numeric value rather than a display string. Worth sampling the "
                        f"field's real values (e.g. esri-explore.py values <url> {attr_value}) and "
                        f"adding a `map` if it turns out to be coded.",
                    )
                )

        walk_functions(attr_value, path, attr_name, findings)


def lint_source(data, findings, field_freq):
    layers = data.get("layers")
    if not isinstance(layers, dict):
        return
    for layer_type, layer_list in layers.items():
        if not isinstance(layer_list, list):
            continue
        for i, layer in enumerate(layer_list):
            if not isinstance(layer, dict):
                continue
            lint_conform(layer.get("conform"), layer_type, i, layer.get("protocol"), findings, field_freq)


def parse_source(path):
    """Parse one source JSON file. Returns (data, None) or (None, error-message)."""
    try:
        text = path.read_text()
    except OSError as e:
        return None, f"could not read file: {e}"
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    if not isinstance(data, dict):
        return None, "top-level JSON value is not an object"
    return data, None


def lint_file(path, field_freq):
    """Return a list of Finding for one source JSON file (or a single PARSE_ERROR finding)."""
    data, error = parse_source(path)
    if error:
        return [Finding(PARSE_ERROR, "-", error)]
    findings = []
    lint_source(data, findings, field_freq)
    return findings


def build_field_frequency(sources_dir):
    """Corpus-wide count of how many ESRI address sources use each bare
    number/postcode field name (lowercased), for the rule 2 rarity gate.
    Always scans the full corpus regardless of which files are being linted,
    since rarity is a property of the whole corpus, not of the lint target.
    """
    freq = {"number": {}, "postcode": {}}
    if not sources_dir.is_dir():
        return freq
    for path in sources_dir.rglob("*.json"):
        data, error = parse_source(path)
        if error or not isinstance(data, dict):
            continue
        layers = data.get("layers")
        if not isinstance(layers, dict):
            continue
        for layer in layers.get("addresses", []) or []:
            if not isinstance(layer, dict) or layer.get("protocol") != "ESRI":
                continue
            conform = layer.get("conform")
            if not isinstance(conform, dict):
                continue
            for attr_name in NUMERIC_LEAK_ATTRS:
                value = conform.get(attr_name)
                if isinstance(value, str):
                    key = value.lower()
                    freq[attr_name][key] = freq[attr_name].get(key, 0) + 1
    return freq


def repo_root():
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, check=True,
        )
        return Path(out.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return Path(__file__).resolve().parent.parent.parent


def git_ref_exists(root, ref):
    return subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", ref],
        cwd=root, capture_output=True,
    ).returncode == 0


def files_from_git_diff(root, args_list):
    out = subprocess.run(
        ["git", "diff"] + args_list,
        cwd=root, capture_output=True, text=True, check=True,
    ).stdout
    return [root / line for line in out.splitlines() if line.strip()]


def resolve_files(args, root):
    if args.staged:
        files = files_from_git_diff(root, ["--cached", "--name-only", "--", "sources/"])
    elif args.changed:
        base = None
        for candidate in ("origin/master", "master"):
            if git_ref_exists(root, candidate):
                base = candidate
                break
        if base is None:
            print("ERROR: --changed needs a 'master' or 'origin/master' ref to diff against", file=sys.stderr)
            sys.exit(2)
        files = files_from_git_diff(root, [f"{base}...HEAD", "--name-only", "--", "sources/"])
    elif args.paths:
        files = []
        for p in args.paths:
            matches = glob.glob(p, recursive=True)
            if matches:
                files.extend(Path(m) for m in matches)
            elif Path(p).exists():
                files.append(Path(p))
            else:
                print(f"WARNING: no match for {p!r}", file=sys.stderr)
    else:
        files = sorted((root / "sources").rglob("*.json"))

    # Only lint .json files that actually exist (git diff can list deletions).
    return [f for f in files if f.suffix == ".json" and f.exists()]


def main():
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "paths", nargs="*",
        help="specific source JSON file paths or globs to lint (default: all of sources/**/*.json)",
    )
    parser.add_argument(
        "--staged", action="store_true",
        help="lint only files staged for commit (git diff --cached --name-only)",
    )
    parser.add_argument(
        "--changed", action="store_true",
        help="lint only files changed vs. origin/master or master (git diff --name-only <base>...HEAD)",
    )
    args = parser.parse_args()

    if args.staged and args.changed:
        parser.error("--staged and --changed are mutually exclusive")

    root = repo_root()
    files = resolve_files(args, root)
    field_freq = build_field_frequency(root / "sources")

    total_bug = 0
    total_warn = 0
    total_parse_error = 0

    for path in files:
        findings = lint_file(path, field_freq)
        if not findings:
            continue

        try:
            display_path = path.relative_to(Path.cwd())
        except ValueError:
            display_path = path

        print(f"{display_path}")
        for f in findings:
            if f.severity == BUG:
                total_bug += 1
            elif f.severity == WARN:
                total_warn += 1
            else:
                total_parse_error += 1
            marker = f"[{f.severity}]"
            if f.severity == PARSE_ERROR:
                print(f"  {marker} {f.message}")
            else:
                print(f"  {marker} {f.path}: {f.message}")
        print()

    print(
        f"Scanned {len(files)} file(s): {total_bug} bug(s), {total_warn} warning(s), "
        f"{total_parse_error} parse error(s)."
    )

    sys.exit(1 if total_bug else 0)


if __name__ == "__main__":
    main()
