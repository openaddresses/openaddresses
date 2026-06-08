# OpenAddresses Development Guide

This document explains how the OpenAddresses ecosystem is structured, how data flows through it, and how to work on any part of it.

## Overview

OpenAddresses is made up of several interconnected repositories:

| Repository | Purpose |
| ---------- | ------- |
| [`openaddresses/openaddresses`](https://github.com/openaddresses/openaddresses) | Source definition JSON files (`sources/`) and complex preprocessing scripts (`scripts/`) |
| [`openaddresses/batch`](https://github.com/openaddresses/batch) | AWS infrastructure, API server, and orchestration tasks that run the weekly data pipeline |
| [`openaddresses/batch-machine`](https://github.com/openaddresses/batch-machine) | Python library that downloads and conforms individual data sources |

---

## Repository: `openaddresses` (this repo)

### Source definition files (`sources/`)

The `sources/` directory is the heart of the project. Each `.json` file describes a single geographic data source — where to download it, what format it's in, and how to map its fields to the OpenAddresses output schema.

Files are organized by country and region:

```
sources/{country}/{region}/{source}.json
```

For example:
- `sources/us/ca/san_francisco.json` — City and County of San Francisco
- `sources/us/ca/alameda.json` — Alameda County, California
- `sources/nz/countrywide.json` — New Zealand (national)

Each source file has two key parts:

**`data`** — A URL pointing to the raw data to download. This can be:
- A direct HTTP/FTP link to a ZIP, CSV, shapefile, GeoJSON, GDB, or GeoPackage file
- An ESRI ArcGIS Feature Service URL (use `"protocol": "ESRI"`)
- A URL to a file previously uploaded to the [OpenAddresses upload service](https://batch.openaddresses.io/upload) (used when the original source requires complex preprocessing — see [Scripts](#scripts-scripts) below)

**`conform`** — A dictionary telling `batch-machine` how to map the source's fields to OpenAddresses output columns. For addresses these are `number`, `street`, `unit`, `city`, `district`, `region`, `postcode`, `id`, and `accuracy`.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full reference on source JSON syntax, conform tags, and attribute functions.

### Validating source files locally

Source files are validated against a JSON Schema at `schema/source_schema_v2.json`. Validation runs automatically via [pre-commit](https://pre-commit.com/) on every commit, and in CI on every pull request.

To run validation manually:

```bash
npm install
npm test
```

Or install and run pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### Scripts (`scripts/`)

Some data sources are too complex to be handled by `batch-machine`'s built-in conform logic — for example, a national ZIP file containing hundreds of per-county CSVs that need to be merged and filtered. The `scripts/` directory contains one-off Python and JavaScript scripts for these sources.

**Scripts are not run automatically.** A contributor runs the script manually, uploads the result to the [OpenAddresses upload service](https://batch.openaddresses.io/upload) to get a stable URL, and then updates the corresponding source JSON file's `data` field to point at that URL. The output file is what `batch-machine` will eventually process.

Each script subdirectory generally mirrors the `sources/` directory structure (e.g., `scripts/us/fl/clean_fl_statewide.py`). The `scripts/README.md` has more detail.

---

## Repository: `batch-machine`

[`batch-machine`](https://github.com/openaddresses/batch-machine) is the Python library that does the actual work of downloading and transforming a single data source. It is used both during the weekly production pipeline and when testing individual sources locally.

### How it works

For each source layer, `batch-machine` runs two phases:

1. **Cache** (`openaddr/cache.py`) — Downloads the data from the URL in `data`. Supports `http`, `ftp`, and `ESRI` protocols. For ESRI sources it uses [`esridump`](https://github.com/openaddresses/pyesridump) to fetch all features as GeoJSON.

2. **Conform** (`openaddr/conform.py`) — Reads the downloaded file (shapefile, CSV, GeoJSON, GDB, GeoPackage, GML) using GDAL/OGR, applies the `conform` mapping from the source JSON to produce a standardized GeoJSON file, and writes output columns like `number`, `street`, `unit`, etc.

The output is a line-delimited GeoJSON file plus a preview image and (optionally) a PMTiles slippy map.

### Running locally with Docker (recommended)

Using the Docker image guarantees the same GDAL version used in production:

```bash
cd /path/to/batch-machine
docker build -t batch-machine .
docker run -it batch-machine bash
```

Inside the container, run a source with:

```bash
openaddr-process-one \
  --layer addresses \
  --layersource county \
  /path/to/sources/us/ca/san_francisco.json \
  /tmp/output
```

`--layer` is one of `addresses`, `parcels`, `buildings`, or `centerlines`.
`--layersource` is the `name` field inside the layer array in the source JSON.

To write output to your host machine, mount a volume:

```bash
docker run -it \
  -v /path/to/sources:/sources \
  -v /tmp/oa-output:/output \
  batch-machine \
  openaddr-process-one --layer addresses --layersource county /sources/us/ca/san_francisco.json /output
```

### Running locally without Docker

Install [GDAL](https://gdal.org/) (must match the version pinned in `setup.py`) and [Tippecanoe](https://github.com/felt/tippecanoe), then:

```bash
cd /path/to/batch-machine
python3 -m venv venv
source venv/bin/activate
pip install -e .
openaddr-process-one --layer addresses --layersource county /path/to/source.json /tmp/output
```

### Output files

After a successful run, `batch-machine` writes several files to the output directory:

| File | Description |
| ---- | ----------- |
| `output.geojson` | Line-delimited GeoJSON with all features in the standardized schema |
| `preview.png` | A rasterized preview image of the data extent |
| `slippymap.pmtiles` | A PMTiles file for interactive map preview |
| `output.txt` | Full processing log |
| `state.json` | Machine-readable summary: feature count, source problems, cache fingerprint, etc. |

### Acceptance tests

Source files can include inline acceptance tests in the `test` key. These run during processing and fail the job if outputs don't match expectations. This is useful for complex `conform` functions where a regression could silently produce wrong data.

Example:
```json
"test": {
    "enabled": true,
    "acceptance-tests": [{
        "description": "address with unit",
        "inputs": { "FULL_ADDR": "102 East Maple St Apt 4A" },
        "expected": { "number": "102", "street": "East Maple St", "unit": "Apt 4A" }
    }]
}
```

---

## Repository: `batch`

[`batch`](https://github.com/openaddresses/batch) contains the AWS infrastructure and application code that orchestrates the weekly production pipeline. It is not needed to contribute source files or test individual sources.

### Components

| Component | Description |
| --------- | ----------- |
| `api/` | Node.js/Express API server — powers [batch.openaddresses.io](https://batch.openaddresses.io) |
| `api/web/` | React frontend for the batch website |
| `task/` | Node.js task runners that are invoked as AWS Batch jobs |
| `cloudformation/` | AWS CloudFormation templates that define all infrastructure |
| `lambda/` | AWS Lambda functions for scheduled triggers |

### Weekly pipeline schedule

The pipeline runs on a fixed AWS EventBridge (CloudWatch Events) schedule:

| Day | Time (UTC) | Job | Description |
| --- | ---------- | --- | ----------- |
| Friday | 12:00 | `sources` | Clones the `openaddresses` repo, submits an AWS Batch job for every source layer, runs `batch-machine` on each one |
| Sunday | 12:00 | `collect` | Aggregates all successful per-source outputs into downloadable country/region collection archives, uploads to S3 and Cloudflare R2 |
| Sunday | 18:00 | `fabric` | Builds the global tiled map (PMTiles) that powers the map view on the website |

The `sources` run uses whichever branch is configured in the `Branch` CloudFormation parameter (normally `master`).

### Per-job task flow (`task/task.js`)

Each individual source job:
1. Pulls the source JSON from S3 (placed there by the `sources` task)
2. Runs `openaddr-process-one` from `batch-machine` inside a Docker container
3. Uploads the output files to S3 (`s3://v2.openaddresses.io/<stack>/job/<job_id>/`)
4. Reports status back to the API

### Collection build (`task/collect.js`)

After all jobs in a run complete, the `collect` task:
1. Downloads the per-job GeoJSON outputs from S3
2. Merges them into per-country and per-region ZIP archives
3. Uploads the archives to both S3 and Cloudflare R2

These are the files users download from [batch.openaddresses.io](https://batch.openaddresses.io).

### Tiled map build (`task/fabric.js`)

The `fabric` task downloads the aggregated GeoJSON, runs [Tippecanoe](https://github.com/felt/tippecanoe) to build PMTiles at the appropriate zoom levels for each layer type, and uploads the result to R2.

---

## Pull Request CI

When you open a pull request against `openaddresses/openaddresses`, an automated CI process runs any source files that changed. This is handled by `ci/run_changed_sources.py`.

### What it does

1. Fetches the list of changed files in the PR from the GitHub API
2. For each changed `sources/*.json` file, compares each layer against the `master` branch to identify which layer sources are new or modified
3. Runs `openaddr-process-one` on each changed layer source
4. Uploads the outputs (GeoJSON, preview image, PMTiles, log) to Cloudflare R2
5. Posts a comment on the PR with a results table containing links to:
   - A preview image of the data
   - An interactive map (via Protomaps PMTiles viewer)
   - The full processing log

### Reading the PR comment

The comment table will show one of:
- ✅ `N features` — Processing succeeded with N output features
- ✅ `Skipped` — The source has `skip: true` set
- ❌ `Failed` — `batch-machine` returned an error (check the Log link)
- ❌ `No features` — Processing ran but produced zero output features
- ❌ `<source problem>` — A known problem like `Missing conform object` or `Could not download source data`

> **Note:** The CI process is separate from the legacy `batch` API webhook integration. As of 2024, PR testing is handled entirely by the GitHub Actions workflow in this repository calling `ci/run_changed_sources.py` directly, rather than routing through the batch API.

---

## Code style

There is no single enforced style guide across all repositories, but please follow the conventions below so that patches are easy to review.

### Python (`batch-machine`, `ci/`)

Format Python code with [Black](https://black.readthedocs.io/) before submitting a pull request. Black is the formatter used in the Python-based projects in the OpenAddresses organisation (see `batch-py/pyproject.toml`).

```bash
pip install black
black ci/run_changed_sources.py          # single file
black openaddr/                          # whole package
```

The default Black settings are fine; if a project has a `[tool.black]` section in `pyproject.toml` (e.g. `line-length = 100`) use that.

For the `ci/` scripts in this repo, no `pyproject.toml` exists — plain `black` defaults (88-character line length) are acceptable.

### JavaScript / Node.js (`batch`, `openaddresses`)

All JavaScript in the project is linted with [ESLint](https://eslint.org/) using a shared ruleset defined in each repo's `eslint.config.js`. The key rules are:

- 4-space indentation
- Single quotes
- Semicolons required
- No trailing commas
- `const`/`let` only — no `var`
- ES module syntax (`import`/`export`)

Run the linter before submitting:

```bash
npm run lint          # from the repo root, or from api/ in batch
```

When in doubt, match the formatting of the file you are editing. The ESLint config is the authoritative reference.

### Source JSON files (`sources/`)

JSON formatting is enforced by the pre-commit hooks:

- 4-space indentation
- No trailing commas
- No blank lines
- No `null` or empty-string values — omit the key entirely instead

The pre-commit hooks will catch basic JSON errors and schema violations automatically. See [Validating source files locally](#validating-source-files-locally).

---

## Data flow summary

```
sources/*.json          ← contributors edit these
       │
       ▼
batch-machine           ← downloads + conforms each source
(openaddr-process-one)
       │
       ├── PR CI        ← runs on pull requests, posts results as PR comment
       │
       └── Weekly run   ← runs every Friday on AWS Batch
              │
              ▼
         per-job outputs on S3/R2
              │
              ▼
         collect task   ← Sunday: merges into country/region archives
              │
              ▼
         batch.openaddresses.io downloads
              │
              ▼
         fabric task    ← Sunday: builds tiled map (PMTiles)
              │
              ▼
         openaddresses.io map
```

---

## Using an LLM to contribute

Many contributors use an AI coding assistant (Claude, Copilot, ChatGPT, Cursor, etc.) to help write or update source files. This works well because source JSON is highly structured, but LLMs do make characteristic mistakes in this repo. Here is how to get good results.

### Give the LLM the right context

AI assistants work best when they can read the actual schema and real examples. Before asking for a new source file, point the assistant at:

- `CONTRIBUTING.md` — the full reference for every key and conform function
- `ATTRIBUTE_FUNCTIONS.md` — detailed examples of every conform function
- `schema/layers/address_conform.json` — the authoritative list of valid conform keys
- An existing source of the same type (e.g. another ESRI/shapefile/CSV source in the same country)

For tools that automatically read a `CLAUDE.md` file (Claude Code, Cursor, and others), this repo includes one at the root. It gives a compact summary of the schema rules, the valid protocol/format combinations, and common mistakes — LLMs that read it before generating a source will make far fewer errors.

### Common LLM mistakes and how to catch them

**Always run `npm test` on AI-generated source files.** The schema uses `additionalProperties: false` everywhere, so any invented key will fail immediately. Common things LLMs get wrong:

- **Wrong `protocol` value.** Only `"http"`, `"ftp"`, and `"ESRI"` are valid. LLMs sometimes write `"https"`, `"HTTP"`, or `"rest"`. The value is case-sensitive.
- **Wrong `format` for ESRI sources.** ESRI Feature/Map Services always produce GeoJSON inside `batch-machine`. The correct conform is always `"format": "geojson"` — not `"shapefile"` or `"esri"`.
- **Adding `lon`/`lat` to non-CSV sources.** These conform keys only apply when `format` is `csv`. LLMs frequently add them to shapefile or ESRI sources where they are invalid.
- **Hallucinated field names.** LLMs may guess plausible-sounding field names like `HOUSE_NUMBER` or `STREET_NAME` when the actual field is `HSE_NBR` or `ST_NM`. Always verify field names from the source (ESRI `?f=json` metadata, a CSV header row, a shapefile's `.dbf`, etc.) before accepting AI-generated conform mappings.
- **Inventing schema keys.** The schema is strict. Keys like `"type"`, `"tags"`, `"source"`, or `"fields"` do not exist. `npm test` will catch these.
- **Omission of `"format"` in conform.** The schema does not require it, but `batch-machine` needs it to know how to read the file. Always include it.

### Workflow for adding a source with AI help

1. Find the upstream data source and note the URL, format, and available field names.
2. Ask the LLM to draft the source JSON, providing the actual field names and format you found.
3. Run `npm test` — fix any schema errors the LLM introduced.
4. Run the source locally with `batch-machine` to verify it actually produces features (see [Running locally with Docker](#running-locally-with-docker-recommended)).
5. Open the pull request — CI will run the source and post a preview with a feature count and map.

The CI preview is the ground truth. A source that validates against the schema but produces zero features or a processing error still needs work.

---

## Where to start

### Adding or fixing a source

1. Find or create the source JSON file in `sources/`
2. Test it locally with `batch-machine` (see [Running locally with Docker](#running-locally-with-docker-recommended))
3. Open a pull request — CI will run the source and post a preview in the PR comments
4. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for full source JSON reference

### Debugging a source that fails in production

1. Find the failed job on [batch.openaddresses.io](https://batch.openaddresses.io) and open its log
2. Reproduce locally: copy the source JSON, run `openaddr-process-one` with the same `--layer` and `--layersource` arguments
3. Common issues:
   - The upstream data URL changed or went offline — update `data` to a new URL, or upload a cached copy to the [upload service](https://batch.openaddresses.io/upload)
   - Field names in the source changed — update the `conform` mapping
   - The data format changed — update `format` and related conform tags

### Working on `batch-machine` (the processing library)

```bash
cd /path/to/batch-machine
docker build -t batch-machine .
docker run -it batch-machine python3 test.py
```

Tests live in `openaddr/tests/`. They use local fixture data so no network access is required.

### Working on the `batch` API or website

See the [`batch` README](https://github.com/openaddresses/batch#development) for instructions on cloning the production database locally and running the API and UI in development mode.
