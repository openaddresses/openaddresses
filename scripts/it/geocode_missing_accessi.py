"""
Backfill missing CoordX/CoordY in an ANNCSU INDIR_ITA export, rebuild the parquet
with a geometry column, and join in comune/provincia/regione from the ISTAT comuni
reference (replaces the old countrywide.py, which did the ISTAT join separately).

Pipeline, run in order:
    1. harvest              query the live ANNCSU "accessi" API per street
    2. merge                apply harvested coords, add geometry + comune/provincia/regione
    3. backfill-historical  fill remaining gaps from an older GEO dump (e.g. ivandorte/
                             anncsu_dump) - all historical points are passed through as-is
    4. export-csv           write the final parquet to CSV, rewriting COORD_X_COMUNE/
                             COORD_Y_COMUNE as plain dot-decimal numbers for consumers
                             (e.g. OpenAddresses conform) that can't parse ANNCSU's
                             comma-decimal convention

API docs: https://anncsu.open.agenziaentrate.gov.it/age-inspire/opendata/anncsu/querydata.php?help_show

Usage:
    python geocode_missing_accessi.py harvest --input INDIR_ITA_20260703.csv --cache accessi_cache.jsonl
    python geocode_missing_accessi.py merge   --input INDIR_ITA_20260703.csv --cache accessi_cache.jsonl --output step2.parquet
    python geocode_missing_accessi.py backfill-historical --input step2.parquet --historical INDIR_ITA_20250128_GEO.parquet --output INDIR_ITA_20260703_GEO_final.parquet
    python geocode_missing_accessi.py export-csv --input INDIR_ITA_20260703_GEO_final.parquet --output INDIR_ITA_20260703_GEO_final.csv

harvest is resumable: rerun the same command and it skips streets already
recorded as success in the cache file, retrying only failures/missing ones.
"""

import argparse
import asyncio
import json
import os
import time

import aiohttp
import duckdb

API_URL = "https://anncsu.open.agenziaentrate.gov.it/age-inspire/opendata/anncsu/querydata.php"
CONCURRENCY = 15          # server throughput caps out around ~12 req/s regardless of concurrency
REQUEST_TIMEOUT = 30
MAX_RETRIES = 3

ISTAT_COMUNI_URL = "https://www.istat.it/storage/codici-unita-amministrative/Elenco-comuni-italiani.xlsx"


def load_missing_odonimi(input_path):
    con = duckdb.connect()
    rows = con.sql(f"""
        SELECT DISTINCT PROGRESSIVO_NAZIONALE
        FROM read_csv_auto('{input_path}', sample_size=-1)
        WHERE COORD_X_COMUNE IS NULL OR COORD_X_COMUNE = ''
    """).fetchall()
    return [r[0] for r in rows]


def load_cached_ids(cache_path):
    done = set()
    if not os.path.exists(cache_path):
        return done
    with open(cache_path) as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("success"):
                done.add(rec["progressivoodonimo"])
    return done


async def fetch_one(session, sem, pid):
    async with sem:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                async with session.get(
                    API_URL,
                    params={"resource": "accessi", "progressivoodonimo": pid, "accesso": ""},
                    timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
                ) as resp:
                    data = await resp.json()
                    if data.get("success"):
                        return {
                            "progressivoodonimo": pid,
                            "success": True,
                            "records": data["result"]["records"],
                        }
                    return {"progressivoodonimo": pid, "success": False, "error": data.get("detail")}
            except Exception as e:
                if attempt == MAX_RETRIES:
                    return {"progressivoodonimo": pid, "success": False, "error": str(e)}
                await asyncio.sleep(2 ** attempt)


async def harvest_async(ids, cache_path, concurrency):
    sem = asyncio.Semaphore(concurrency)
    queue = asyncio.Queue()

    async def writer():
        with open(cache_path, "a") as f:
            n = 0
            t0 = time.time()
            while True:
                rec = await queue.get()
                if rec is None:
                    break
                f.write(json.dumps(rec) + "\n")
                f.flush()
                n += 1
                if n % 2000 == 0:
                    rate = n / (time.time() - t0)
                    print(f"  {n}/{len(ids)} done, {rate:.1f} req/s", flush=True)

    async def worker(pid):
        rec = await fetch_one(session, sem, pid)
        await queue.put(rec)

    async with aiohttp.ClientSession() as session:
        writer_task = asyncio.create_task(writer())
        await asyncio.gather(*[worker(pid) for pid in ids])
        await queue.put(None)
        await writer_task


def cmd_harvest(args):
    print(f"Loading unique streets with missing coordinates from {args.input} ...")
    all_ids = load_missing_odonimi(args.input)
    print(f"  {len(all_ids)} unique streets need geocoding")

    already_done = load_cached_ids(args.cache)
    todo = [pid for pid in all_ids if pid not in already_done]
    print(f"  {len(already_done)} already cached, {len(todo)} remaining")

    if not todo:
        print("Nothing to harvest.")
        return

    est_seconds = len(todo) / 12
    print(f"Estimated time at ~12 req/s: {est_seconds/3600:.1f} hours")
    asyncio.run(harvest_async(todo, args.cache, args.concurrency))
    print("Harvest complete.")


def cmd_merge(args):
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")
    con.sql("INSTALL excel; LOAD excel;")
    con.sql("INSTALL httpfs; LOAD httpfs;")

    print(f"Loading ISTAT comuni reference from {args.istat_xlsx} ...")
    # Sardinia's provinces have been renumbered several times (1995/2006/2010/2017), and
    # ANNCSU's CODICE_ISTAT for Sardinian comuni is stuck on an old scheme that no longer
    # appears in the current ISTAT list at all - only in its own historical-numbering
    # columns. Matching against those too is what actually closes the join for Sardinia.
    con.sql(f"""
        CREATE TABLE istat_comuni AS
        SELECT
            "Codice Comune formato alfanumerico" AS codice_istat,
            "Denominazione in italiano" AS comune,
            "Denominazione dell'Unità territoriale sovracomunale 
(valida a fini statistici)" AS provincia,
            "Denominazione Regione" AS regione,
            LPAD(CAST("Codice Comune numerico con 103 Province (dal 1995 al 2005)" AS BIGINT)::VARCHAR, 6, '0') AS hist_103,
            LPAD(CAST("Codice Comune numerico con 107 Province (dal 2006 al 2009)" AS BIGINT)::VARCHAR, 6, '0') AS hist_107a,
            LPAD(CAST("Codice Comune numerico con 110 Province (dal 2010 al 2016)" AS BIGINT)::VARCHAR, 6, '0') AS hist_110,
            LPAD(CAST("Codice Comune numerico con 107 Province (dal 2017 al 2025)" AS BIGINT)::VARCHAR, 6, '0') AS hist_107b
        FROM read_xlsx('{args.istat_xlsx}', all_varchar=true)
    """)

    print(f"Loading cache from {args.cache} ...")
    con.sql(f"""
        CREATE TABLE accessi_raw AS
        SELECT * FROM read_json_auto('{args.cache}')
        WHERE success = true
    """)
    con.sql("""
        CREATE TABLE accessi_lookup AS
        SELECT
            progressivoodonimo,
            CAST(rec.Progressivo_nazionale_accesso AS BIGINT) AS progressivo_accesso,
            rec.CoordX AS coordx_raw,
            rec.CoordY AS coordy_raw
        FROM accessi_raw, UNNEST(records) AS t(rec)
        WHERE rec.CoordX IS NOT NULL AND rec.CoordX != ''
          AND rec.CoordY IS NOT NULL AND rec.CoordY != ''
    """)
    n_lookup = con.sql("SELECT COUNT(*) FROM accessi_lookup").fetchone()[0]
    print(f"  {n_lookup} recoverable coordinate records in cache")

    print(f"Merging into {args.input}, joining ISTAT comuni, and writing {args.output} ...")
    con.sql(f"""
        COPY (
            SELECT
                src.* EXCLUDE (COORD_X_COMUNE, COORD_Y_COMUNE),
                COALESCE(src.COORD_X_COMUNE, lk.coordx_raw) AS COORD_X_COMUNE,
                COALESCE(src.COORD_Y_COMUNE, lk.coordy_raw) AS COORD_Y_COMUNE,
                CASE WHEN COALESCE(src.COORD_X_COMUNE, lk.coordx_raw) IS NOT NULL
                          AND COALESCE(src.COORD_X_COMUNE, lk.coordx_raw) != ''
                          AND COALESCE(src.COORD_Y_COMUNE, lk.coordy_raw) IS NOT NULL
                          AND COALESCE(src.COORD_Y_COMUNE, lk.coordy_raw) != ''
                     THEN ST_Point(
                         CAST(REPLACE(COALESCE(src.COORD_X_COMUNE, lk.coordx_raw), ',', '.') AS DOUBLE),
                         CAST(REPLACE(COALESCE(src.COORD_Y_COMUNE, lk.coordy_raw), ',', '.') AS DOUBLE)
                     )
                END AS geometry,
                ic.comune AS COMUNE,
                ic.provincia AS PROVINCIA,
                ic.regione AS REGIONE
            FROM read_csv_auto('{args.input}', sample_size=-1) src
            LEFT JOIN accessi_lookup lk
                ON src.PROGRESSIVO_NAZIONALE = lk.progressivoodonimo
               AND src.PROGRESSIVO_ACCESSO = lk.progressivo_accesso
            LEFT JOIN istat_comuni ic
                ON src.CODICE_ISTAT = ic.codice_istat
                OR src.CODICE_ISTAT = ic.hist_103
                OR src.CODICE_ISTAT = ic.hist_107a
                OR src.CODICE_ISTAT = ic.hist_110
                OR src.CODICE_ISTAT = ic.hist_107b
        ) TO '{args.output}' (FORMAT PARQUET)
    """)

    stats = con.sql(f"""
        SELECT COUNT(*) total, COUNT(geometry) with_geom, COUNT(COMUNE) with_comune
        FROM '{args.output}'
    """).fetchone()
    print(f"Done. {stats[1]}/{stats[0]} rows have geometry ({stats[1]/stats[0]*100:.1f}%), "
          f"{stats[2]}/{stats[0]} rows have comune/provincia/regione ({stats[2]/stats[0]*100:.1f}%).")


def cmd_backfill_historical(args):
    """
    Fill remaining NULL geometry from an older GEO dump (e.g. ivandorte/anncsu_dump's
    INDIR_ITA_20250128_GEO.parquet). All historical points are passed through as-is.

    An earlier version of this step tried to detect and drop "bogus placeholder"
    clusters (many addresses piled onto the same ~10m spot) before backfilling. Manual
    inspection of a sample showed most of those flagged clusters are legitimate, if
    low-precision, interpolated geocodes from a time when the ANNCSU API served that
    fallback — it appears to have stopped serving them since, which is why they're
    absent from the live API and from the current CSV, not because they were wrong. That
    data still has value for backfill purposes, so we no longer filter it here.
    """
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")

    print(f"Loading historical dump {args.historical} ...")
    con.sql(f"""
        CREATE TABLE clean_historical AS
        SELECT PROGRESSIVO_NAZIONALE, PROGRESSIVO_ACCESSO, MIN(geometry) AS geometry
        FROM '{args.historical}'
        WHERE geometry IS NOT NULL
        GROUP BY PROGRESSIVO_NAZIONALE, PROGRESSIVO_ACCESSO
    """)

    before = con.sql(f"SELECT COUNT(*) t, COUNT(geometry) g FROM '{args.input}'").fetchone()

    print(f"Filling remaining NULL geometry in {args.input} from historical points, writing {args.output} ...")
    # Also backfill COORD_X_COMUNE/COORD_Y_COMUNE (comma-decimal, matching the source
    # CSV's own format) - not just geometry - so consumers that read the flat columns
    # instead of geometry (e.g. a plain CSV export) still see the recovered coordinate.
    con.sql(f"""
        COPY (
            SELECT
                src.* EXCLUDE (geometry, COORD_X_COMUNE, COORD_Y_COMUNE),
                COALESCE(src.COORD_X_COMUNE, REPLACE(CAST(ST_X(ch.geometry) AS VARCHAR), '.', ',')) AS COORD_X_COMUNE,
                COALESCE(src.COORD_Y_COMUNE, REPLACE(CAST(ST_Y(ch.geometry) AS VARCHAR), '.', ',')) AS COORD_Y_COMUNE,
                COALESCE(src.geometry, ch.geometry) AS geometry
            FROM '{args.input}' src
            LEFT JOIN clean_historical ch
                ON src.PROGRESSIVO_NAZIONALE = ch.PROGRESSIVO_NAZIONALE
               AND src.PROGRESSIVO_ACCESSO = ch.PROGRESSIVO_ACCESSO
        ) TO '{args.output}' (FORMAT PARQUET)
    """)

    after = con.sql(f"SELECT COUNT(*) t, COUNT(geometry) g FROM '{args.output}'").fetchone()
    print(f"Done. geometry coverage {before[1]}/{before[0]} ({before[1]/before[0]*100:.1f}%) "
          f"-> {after[1]}/{after[0]} ({after[1]/after[0]*100:.1f}%).")


def cmd_export_csv(args):
    """
    Export the final parquet to CSV. COORD_X_COMUNE/COORD_Y_COMUNE match ANNCSU's own
    comma-decimal convention in the parquet, but a comma decimal separator doesn't parse
    as a number under standard (dot-decimal) CSV/float parsing - which breaks consumers
    like OpenAddresses' conform pipeline. So for this final CSV, we rewrite those same
    two columns as plain dot-decimal numbers (straight from the geometry column, which is
    already a clean float) instead of adding separate lon/lat columns.

    Also renames LOCALITA' to LOCALITA - ANNCSU's own column name has a literal
    apostrophe in it, which is a plausible trigger for downstream JSON-generation tools
    that don't expect punctuation in a property key.
    """
    con = duckdb.connect()
    con.sql("INSTALL spatial; LOAD spatial;")

    print(f"Exporting {args.input} to {args.output} with dot-decimal COORD_X_COMUNE/COORD_Y_COMUNE ...")
    con.sql(f"""
        COPY (
            SELECT
                * EXCLUDE (geometry, COORD_X_COMUNE, COORD_Y_COMUNE, "LOCALITA'"),
                ST_X(geometry) AS COORD_X_COMUNE,
                ST_Y(geometry) AS COORD_Y_COMUNE,
                "LOCALITA'" AS LOCALITA
            FROM '{args.input}'
        ) TO '{args.output}' (HEADER, DELIMITER ',')
    """)

    # sample_size=-1: QUOTA is comma-decimal and gets quoted (e.g. "343,3") when it
    # contains the delimiter, but quoted fields are rare enough that DuckDB's default
    # small-sample auto-detection can miss the quote character entirely and misparse.
    stats = con.sql(f"SELECT COUNT(*), COUNT(COORD_X_COMUNE) FROM read_csv_auto('{args.output}', sample_size=-1)").fetchone()
    print(f"Done. {stats[1]}/{stats[0]} rows have coordinates.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_harvest = sub.add_parser("harvest", help="Fetch missing coordinates from the ANNCSU accessi API")
    p_harvest.add_argument("--input", required=True, help="Source INDIR_ITA CSV path")
    p_harvest.add_argument("--cache", required=True, help="JSONL cache file to write/resume from")
    p_harvest.add_argument("--concurrency", type=int, default=CONCURRENCY)
    p_harvest.set_defaults(func=cmd_harvest)

    p_merge = sub.add_parser(
        "merge",
        help="Merge harvested coordinates back into a parquet with geometry and comune/provincia/regione",
    )
    p_merge.add_argument("--input", required=True, help="Source INDIR_ITA CSV path")
    p_merge.add_argument("--cache", required=True, help="JSONL cache file produced by harvest")
    p_merge.add_argument("--output", required=True, help="Output parquet path")
    p_merge.add_argument(
        "--istat-xlsx",
        default=ISTAT_COMUNI_URL,
        help="ISTAT comuni xlsx URL or local path (default: latest ISTAT publication)",
    )
    p_merge.set_defaults(func=cmd_merge)

    p_hist = sub.add_parser(
        "backfill-historical",
        help="Fill remaining NULL geometry (and COORD_X/Y_COMUNE) from an older GEO dump, unfiltered",
    )
    p_hist.add_argument("--input", required=True, help="Parquet produced by merge")
    p_hist.add_argument("--historical", required=True, help="Older GEO parquet to backfill from (must have PROGRESSIVO_NAZIONALE, PROGRESSIVO_ACCESSO, geometry)")
    p_hist.add_argument("--output", required=True, help="Output parquet path")
    p_hist.set_defaults(func=cmd_backfill_historical)

    p_csv = sub.add_parser(
        "export-csv",
        help="Export the final parquet to CSV with plain numeric lon/lat columns for OpenAddresses conform",
    )
    p_csv.add_argument("--input", required=True, help="Parquet produced by backfill-historical")
    p_csv.add_argument("--output", required=True, help="Output CSV path")
    p_csv.set_defaults(func=cmd_export_csv)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
