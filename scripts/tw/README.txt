Taiwan Address Joiner & Reprojector

This script processes Taiwan address point data by:

- Automatically detecting and decoding the input CSV (supports Big5, UTF-8, etc.)
- Joining the data with an official administrative district code table
- Optionally reprojecting coordinates from EPSG:3826 (TWD97 TM2) to EPSG:4326 (WGS84)
- Cleaning and standardizing column names
- Outputting the result as a UTF-8 CSV and zipping the file

------------------------------------------------------------
Requirements

- Python 3.7+
- pandas
- pyproj
- chardet

Install with:
pip install pandas pyproj chardet

------------------------------------------------------------
Usage

python processing.py <input_address_csv> <output_csv> [--code_table CODE_TABLE] [--no-reproject]

Positional Arguments:
- <input_address_csv>: Path to the input Taiwan address CSV file
- <output_csv>: Desired filename for output CSV (a .zip will also be created)

Optional Flags:
- --code_table: Path to a district code table (default: ./Taiwan_county_district_codes.csv)
- --no-reproject: Skip coordinate reprojection; original coordinates will be copied into 4326 columns

------------------------------------------------------------
Example

python processing.py Miaoli_addresses.csv Miaoli_2025_output.csv

This will:
- Decode Miaoli_addresses.csv
- Join it with district codes
- Reproject the coordinates to WGS84
- Save a cleaned CSV and ZIP it

------------------------------------------------------------
Notes

- Input CSVs may use traditional Chinese headers or English equivalents
- Handles malformed areacodes, encoding issues, and missing fields automatically
- Original and reprojected coordinates are retained (x_3826, y_3826, x_4326, y_4326)
- Inputs may still need to be converted to csv or combined from multiple files beforehand

------------------------------------------------------------
Output Format

Final CSV columns:
countycode, areacode, village, neighbor, street, area, lane, alley, number,
x_3826, y_3826, x_4326, y_4326, county, town
