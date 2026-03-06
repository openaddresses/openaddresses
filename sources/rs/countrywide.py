import argparse
from datetime import datetime, timezone
import geopandas
import os
import requests
import shutil
import tempfile
import zipfile


def get_parser():
    parser = argparse.ArgumentParser(
        description='Download and process the Serbian Address Registry dataset from data.gov.rs.\n\n'
                    'IMPORTANT:\n'
                    '- The download only works from an IP address located in Serbia due to geoblocking.\n'
                    '- You can use --extract-dir to skip the download and work with a pre-downloaded ZIP file.',
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        '--download',
        action='store_true',
        help='Download the ZIP file from data.gov.rs (only works from within Serbia).'
    )

    parser.add_argument(
        '--extract-dir',
        type=str,
        help='Directory where the ZIP file "kucni_br_gpkg.zip" is located.\n'
            'If not provided, the file will be extracted from the system temporary directory.'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./output/',
        help='Output directory where processed data will be stored (default: ./output/).'
    )

    return parser


if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    if not args.download and not args.extract_dir:
        parser.error("You must specify at least one of --download or --extract-dir.")

    temp_dir = tempfile.gettempdir()
    extract_dir = args.extract_dir if args.extract_dir else os.path.join(temp_dir, 'extracted')
    os.makedirs(extract_dir, exist_ok=True)

    download_path = os.path.join(extract_dir, 'kucni_br_gpkg.zip')

    # Does NOT work outside of Serbia due to geoblocking.
    if args.download:
        with requests.get('https://data.gov.rs/sr/datasets/r/be7c80e3-206b-46af-b31d-4b9f6ae596f9') as r:
            r.raise_for_status()
            with open(download_path, 'wb') as f:
                f.write(r.content)

    with zipfile.ZipFile(download_path) as zip_ref:
        zip_ref.extractall(extract_dir)

    rs = geopandas.read_file(os.path.join(extract_dir, 'kucni_broj.gpkg'))
    rs.to_crs(epsg=4326, inplace=True)

    rs['latitude'] = rs.geometry.y
    rs['longitude'] = rs.geometry.x

    rs.to_parquet(path=os.path.join(extract_dir, 'kucni_broj.parquet'), index=False)
    rs.to_csv(path_or_buf=os.path.join(extract_dir, 'kucni_broj.csv'), index=False)

    utc_now = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    zip_output_path = os.path.join(args.output, f'kucni_broj_outputs_{utc_now}.zip')
    os.makedirs(args.output, exist_ok=True)
    with zipfile.ZipFile(zip_output_path, 'w') as zipf:
        zipf.write(os.path.join(extract_dir, 'kucni_broj.csv'), arcname='kucni_broj.csv')

    shutil.rmtree(extract_dir, ignore_errors=True)
