import argparse
import csv
import sys
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

# AddressForAll republishes IBGE's CNEFE 2022 countrywide address export,
# already cleaned up and mapped onto the OpenAddresses field names (id,
# region, city, number, street, postcode, lat, lon). This script splits
# that single countrywide file into per-state CSVs, matching the naming
# convention used by the direct-from-IBGE cnefe_2022 script, so they can be
# re-uploaded to the OpenAddresses cache and referenced from sources/br/*.

DOWNLOAD_URL = (
    "https://www.dropbox.com/scl/fi/gbfkot4dtx5u3cl2nktjg/"
    "CNEFE_With_Neighbourhood_20250820.csv?rlkey=7pmirxpl5rwji1kbuodd7yfly&st=b329i8vc&dl=1"
)

STATES_BY_CODE = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}
CODE_BY_STATE = {abbr: code for code, abbr in STATES_BY_CODE.items()}

EXPECTED_HEADER = [
    "id",
    "region",
    "city",
    "number",
    "street",
    "postcode",
    "lat",
    "lon",
    "neighborhood",
]


def download(url: str, dest: Path) -> None:
    if dest.exists():
        print(f"{dest.name} already downloaded. Skipping download.")
        return

    print(f"Downloading {url}...")
    retry_strategy = Retry(total=3)
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    with session.get(url, stream=True, timeout=30) as response:
        if response.status_code != 200:
            print(f"Failed! Status code: {response.status_code} ({response.reason})")
            sys.exit(1)
        total = 0
        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                f.write(chunk)
                total += len(chunk)
        print(f"Done! {total / (1024 * 1024):.2f} MB downloaded.")


def iter_csv_rows(input_path: Path):
    """Yield (header, row) tuples from every CSV in input_path, which may be
    a .zip archive containing one or more CSVs, or a CSV file directly."""
    if input_path.suffix == ".zip":
        with zipfile.ZipFile(input_path, "r") as zf:
            csv_names = [n for n in zf.namelist() if n.lower().endswith(".csv")]
            if not csv_names:
                print(f"No CSV files found inside {input_path}")
                sys.exit(1)
            for name in csv_names:
                print(f"Reading {name} from {input_path.name}...")
                with zf.open(name, "r") as raw:
                    text = (line.decode("utf-8") for line in raw)
                    reader = csv.reader(text)
                    header = next(reader)
                    for row in reader:
                        yield header, row
    else:
        print(f"Reading {input_path.name}...")
        with open(input_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            for row in reader:
                yield header, row


def main():
    parser = argparse.ArgumentParser(
        description="Split the AddressForAll CNEFE 2022 countrywide export into per-state OA CSVs."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=None,
        help="Use a local .zip or .csv file instead of downloading from AddressForAll "
        "(useful for local testing, e.g. the file already downloaded to ~/Downloads).",
    )
    parser.add_argument(
        "--url",
        default=DOWNLOAD_URL,
        help="Override the AddressForAll download URL.",
    )
    parser.add_argument(
        "--download-dir",
        type=Path,
        default=Path("/tmp/cnefe_addressforall"),
        help="Where to store the downloaded zip.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output_addressforall"),
        help="Where to write the per-state CSV/zip files.",
    )
    parser.add_argument(
        "--no-zip",
        action="store_true",
        help="Skip zipping the per-state CSVs (only produce the raw CSV files).",
    )
    args = parser.parse_args()

    start = time.time()

    if args.input is not None:
        input_path = args.input
        if not input_path.exists():
            print(f"Input file not found: {input_path}")
            sys.exit(1)
    else:
        args.download_dir.mkdir(parents=True, exist_ok=True)
        input_path = args.download_dir / Path(urlparse(args.url).path).name
        download(args.url, input_path)

    args.output_dir.mkdir(parents=True, exist_ok=True)

    writers = {}
    files = {}
    counts = {abbr: 0 for abbr in STATES_BY_CODE.values()}
    unknown_regions = {}
    header_checked = False

    print()
    print("Splitting into per-state files")
    print("===============================")

    row_count = 0
    for header, row in iter_csv_rows(input_path):
        if not header_checked:
            if header != EXPECTED_HEADER:
                print(f"WARNING: unexpected header {header}, expected {EXPECTED_HEADER}")
            header_checked = True

        row_count += 1
        if row_count % 5_000_000 == 0:
            print(f"  ...{row_count:,} rows processed")

        region = row[1]
        code = CODE_BY_STATE.get(region)
        if code is None:
            unknown_regions[region] = unknown_regions.get(region, 0) + 1
            continue

        # Fix postcodes that lost a leading zero (CEP is always 8 digits;
        # AddressForAll's export drops the leading zero for some states, e.g. SP).
        postcode = row[5]
        if postcode.isdigit():
            postcode = postcode.zfill(8)
        row[5] = postcode

        if code not in writers:
            out_name = f"{code}_{region}.csv"
            f = open(args.output_dir / out_name, "w", newline="")
            files[code] = f
            writers[code] = csv.writer(f)
            writers[code].writerow(header)

        writers[code].writerow(row)
        counts[region] += 1

    for f in files.values():
        f.close()

    print(f"Done! {row_count:,} total rows processed.")

    if unknown_regions:
        print()
        print(f"WARNING: found rows with unrecognized region codes: {unknown_regions}")

    print()
    print("Row counts by state")
    print("====================")
    for code in sorted(STATES_BY_CODE):
        abbr = STATES_BY_CODE[code]
        print(f"  {code}_{abbr}: {counts[abbr]:,}")

    if not args.no_zip:
        print()
        print("Zipping per-state files")
        print("========================")
        for code, abbr in STATES_BY_CODE.items():
            if counts[abbr] == 0:
                continue
            csv_name = f"{code}_{abbr}.csv"
            zip_path = args.output_dir / f"{code}_{abbr}.zip"
            print(f"Zipping {csv_name}...", end="", flush=True)
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(args.output_dir / csv_name, arcname=csv_name)
            print(" Done!")

    print("===============================")
    print("Finished processing.")
    print(f"Total time: {time.time() - start:.2f} seconds")


if __name__ == "__main__":
    main()
