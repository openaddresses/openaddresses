# OpenAddresses — LLM context

This file is read automatically by AI coding assistants. It gives you the essential facts about this repository so you can contribute accurately without hallucinating field names, inventing schema keys, or writing source files that fail validation.

## What this repo is

A collection of ~2 800 JSON source definition files in `sources/`. Each file tells the processing pipeline (`batch-machine`) where to download geographic data and how to map its fields to the OpenAddresses output schema. No application code runs automatically from this repo — pull requests are tested by CI, and the full dataset is rebuilt weekly on AWS.

## Before you write or edit a source file

1. **Always run `npm test` to validate.** The test suite compiles `schema/source_schema_v2.json` and validates every changed source file. Schema errors will be caught here, not in CI.
2. **Look at an existing source in the same region or of the same type** before writing a new one. Real examples are the best guide. `sources/us/ca/san_francisco.json` is a complete example covering all four layer types.
3. **Do not invent schema keys.** The schema uses `additionalProperties: false` throughout. Unknown keys will fail validation. Every valid key is documented in `CONTRIBUTING.md` and defined in `schema/`.

## Source file structure — the essentials

```json
{
    "schema": 2,
    "coverage": { "country": "us", "state": "ca", "county": "san francisco" },
    "layers": {
        "addresses": [{
            "name": "county",
            "data": "https://...",
            "protocol": "ESRI",
            "conform": {
                "format": "geojson",
                "number": "ADDR_NUM",
                "street": ["ST_PRE_DIR", "ST_NAME", "ST_POS_TYP"]
            }
        }]
    }
}
```

- `schema` must be `2`.
- `coverage.country` is required. `state`/`province`, `county`, `city` are optional but strongly preferred.
- `protocol` is exactly one of: `"http"`, `"ftp"`, `"ESRI"` (case-sensitive).
- `format` in `conform` is exactly one of: `"csv"`, `"geojson"`, `"shapefile"`, `"shapefile-polygon"`, `"gdb"`, `"gpkg"`, `"xml"`.
- **For ESRI sources, always use `"format": "geojson"`** — that is how `batch-machine` receives the dumped features.
- `lon` and `lat` in `conform` are **only for CSV sources**. Omit them for every other format.
- `number` and `street` are required in `addresses` conform. Everything else is optional.
- `pid` is required in `parcels` conform.
- Omit keys with empty or null values — do not set them to `null`, `""`, or `[]`.

## Protocol / format combinations that actually appear in production

| Count | Protocol | Format | Typical use |
|------:|----------|--------|-------------|
| 3368  | ESRI     | geojson | ArcGIS Feature/Map Service |
| 524   | http     | csv     | CSV download |
| 404   | http     | shapefile | Shapefile in ZIP |
| 277   | http     | geojson | GeoJSON download |
| 176   | http     | gdb     | File geodatabase in ZIP |

If you find yourself writing `"protocol": "ESRI"` with `"format": "shapefile"`, stop — that combination is almost certainly wrong.

## Conform: field values and attribute functions

A conform attribute can be:

**A plain field name string:**
```json
"number": "ADDR_NUM"
```

**An array of field names (joined with a space):**
```json
"street": ["ST_PRE_DIR", "ST_NAME", "ST_POS_TYP"]
```

**A function object** — always has a `"function"` key. Valid functions:

| Function | Required keys | What it does |
|----------|--------------|--------------|
| `regexp` | `field`, `pattern`, (optional `replace`) | Regex extract or find-and-replace |
| `map` | `field`, `mapping`, (optional `else`) | Lookup table from source value to output value |
| `join` | `fields`, (optional `separator`) | Join multiple fields with a delimiter |
| `format` | `fields`, `format` | Template string, `$1` `$2` … reference fields positionally |
| `constant` | `value` | Hard-code a fixed string |
| `first_non_empty` | `fields` | Use the first non-empty value from a list of fields |
| `prefixed_number` | `field` | Extract the leading number from "123 Main St" |
| `postfixed_street` | `field` | Extract the street from "123 Main St" |
| `postfixed_unit` | `field` | Extract the trailing unit from "123 Main St Apt 4A" |
| `remove_prefix` | `field`, `field_to_remove` | Remove the value of one field from the start of another |
| `remove_postfix` | `field`, `field_to_remove` | Remove the value of one field from the end of another |
| `chain` | `variable`, `functions` | Pipe output of one function into the next as `variable` |
| `get` | `field`, `index` | Get the nth occurrence of a repeated field (e.g. in XML) |
| `mph_to_kph` | `field` | Convert speed value from mph to km/h |

**Functions cannot be arbitrarily nested** except via `chain`. If you need to apply two transforms to one field, use `chain`.

## Common mistakes to avoid

- **Inventing protocol values.** Only `http`, `ftp`, and `ESRI` are valid. `https` is not a valid protocol — use `http` even for HTTPS URLs.
- **Adding `lon`/`lat` to non-CSV sources.** These keys only belong in `conform` when `format` is `csv`.
- **Forgetting `"format"` in conform.** It is not required by the schema but is required for `batch-machine` to process the source. Always include it.
- **Using `"format": "shapefile"` with ESRI protocol.** ESRI sources always produce GeoJSON. Use `"format": "geojson"`.
- **Trailing commas or blank lines in JSON.** The pre-commit hook will reject these.
- **Setting a key to `null` or `""`** instead of omitting it.
- **Assuming field names without checking.** Field names are case-sensitive and vary between sources. Always verify them from the ESRI service metadata or a data sample before writing the conform.
- **Writing `"protocol": "HTTPS"` or `"protocol": "HTTP"`.** Wrong case. It is `"http"`.

## Verifying an ESRI source

To see the available fields for an ESRI Feature Service layer, append `?f=json` to the service URL:

```
https://example.com/arcgis/rest/services/Addresses/FeatureServer/0?f=json
```

The `fields` array in the response lists every field name and its type. Use those exact names in `conform`.

## Uploading preprocessed data

If a source requires preprocessing (e.g. a script in `scripts/`), upload the result to `https://batch.openaddresses.io/upload` and use the returned URL as the `data` value. Do not commit large data files to this repository.

## Testing your changes

```bash
npm install         # first time only
npm test            # validates all source JSON against the schema
```

The pre-commit hooks (`pre-commit run --all-files`) also check for trailing whitespace, file endings, and JSON syntax errors.

## Key files to read

| File | Purpose |
|------|---------|
| `CONTRIBUTING.md` | Full reference for all source JSON keys, conform tags, and attribute functions |
| `ATTRIBUTE_FUNCTIONS.md` | Detailed documentation and examples for every conform function |
| `schema/source_schema_v2.json` | Root JSON Schema — traces through `schema/layers/` and `schema/util/` |
| `schema/layers/address_conform.json` | Authoritative list of valid address conform keys |
| `sources/us/ca/san_francisco.json` | A complete real-world example covering all four layer types |
