Brazil 2022 census data (via AddressForAll)
============================================

[AddressForAll](https://www.addressforall.org/) republishes IBGE's CNEFE 2022 address export as a single
countrywide CSV, already cleaned up and mapped onto OpenAddresses field names
(`id, region, city, number, street, postcode, lat, lon`). This replaces the need to download and process
53 separate per-state files directly from IBGE (see `../cnefe_2022`).

This script splits that countrywide file into per-state CSVs (and zips), using the same
`{state_code}_{state_abbr}` naming convention as the existing `cnefe_2022` uploads (e.g. `12_AC.zip`, `35_SP.zip`),
so they can be re-uploaded to the OpenAddresses cache and referenced from `sources/br/*/statewide.json`.

It also fixes a data quality issue in the AddressForAll export: postcodes for São Paulo lose their
leading zero (CEP is always 8 digits), which this script restores by zero-padding.

Usage:

    pip install requests
    # Download directly from AddressForAll and split:
    python process_addressforall.py

    # Or use an already-downloaded file (zip or extracted csv) for local testing:
    python process_addressforall.py --input /path/to/ibge_cnefe2022_exp_OpenAddresses.csv.zip
    python process_addressforall.py --input /path/to/ibge_cnefe2022_base1_exp_OpenAddresses.csv

Output is written to `output_addressforall/` (override with `--output-dir`), one `{code}_{ABBR}.csv` and
`{code}_{ABBR}.zip` per state. Pass `--no-zip` to skip the zip step.

Requirements: Python 3 with the `requests` package.

Note: the per-state CSVs already use OpenAddresses-style field names, so the `conform` block for each
state's `sources/br/*/statewide.json` should be much simpler than the direct-from-IBGE version — no
`district`/`unit`/`notes` fields are available in this export, and the id/lat/lon/number/street/city/region/postcode
fields can be mapped directly by name.
