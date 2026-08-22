These scripts scrape parcel boundaries (and, where available, site addresses) from Illinois counties that use WTH Technology's ThinkGIS parcel viewer (e.g. https://gallatinil.wthgis.com/). `lib.js` holds the shared scraping/decoding logic; each subdirectory (`gallatin/`, `mason/`, `pike/`, `richland/`) is a thin per-county config that calls it.

These viewers have no bulk export or REST API. Clicking a parcel calls `tgis/idftr.aspx` with the clicked screen pixel, which is impractical to script at scale. However the same viewer's hover/tooltip code also calls `tgis/getftr.aspx?D=<dsid>&F=<id>&Z=1`, which returns one parcel's attributes and geometry keyed by a small sequential integer id (not a pixel click). `lib.js` walks that id range for a county (probing for the upper bound automatically) and decodes each parcel's delta-encoded polygon (`<poly>` tag - documented inline in `lib.js`, reverse-engineered from `drawPoly5()`/`z192LL()` in the site's own `tgis/tgisProc2.js`) into GeoJSON.

`dsid` is an arbitrary per-county id, not derivable from the subdomain - it only shows up embedded in a real parcel response (e.g. a `DSID=` link, or via a captured browser click). If you need to onboard another WTH-hosted IL county, the fastest way is to click one real parcel in that county's viewer and copy the request as curl (browser devtools → Network tab), same as was done for the 4 here.

Field labels aren't consistent between counties either - some use a `<th class="leftheader">Label</th><td>Value</td>` table, others use `<td class=ftrfld>label</td><td class=ftrval>Value</td>` with different label names (e.g. `taxID` instead of `Parcel Number`). `lib.js`'s `parseFields()` handles both shapes generically; each county's `index.js` just names which label maps to `pid` and (if populated) address.

Run `node index` in a county's directory (no dependencies, needs Node 18+ for global `fetch`) to produce a single `<county>.geojson`. Output goes to `$DATA_DIR` if set, otherwise the OS temp directory - the script prints the full output path when it finishes.

Each feature is a parcel polygon carrying both `pid` and, where that county has an `addressLabel` configured, `address`/`city`/`postcode`. This is one file per county rather than separate parcels/addresses files on purpose: upload it once, then point both the source JSON's `parcels` and `addresses` layers at the same uploaded URL, each with its own `conform` pulling out what it needs - this repo already does that in plenty of sources (e.g. `sources/au/qld/logan_city.json`). Split `address` into `number`/`street` with `prefixed_number`/`postfixed_street` (see `sources/us/mi/mason.json` for the same pattern against a similar parcel-derived source).

| County | dsid | pid field | Site/tax address field |
| --- | --- | --- | --- |
| Gallatin | 10435 | `Parcel Number` | none populated |
| Mason | 7930 | `Parcel Number` | `Site Address` |
| Pike | 10340 | `Parcel Number` | `Site Address` |
| Richland | 823 | `taxID` | `taxPropAddress` + `taxPropCityStZip` (no postcode - Richland's property-address record never carries one, only the owner's mailing zip, which is a different location) |
