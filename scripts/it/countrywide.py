import duckdb
import zipfile
import requests
import io
import os

# Script processes the parquet into a CSV and joins ciyt, district, and region from ISTAT table.


# 1. Download the zip into memory
zip_url = "https://www.istat.it/storage/codici-unita-amministrative/Elenco-codici-statistici-e-denominazioni-delle-unit%C3%A0-territoriali.zip"
response = requests.get(zip_url)
zip_bytes = io.BytesIO(response.content)

# 2. Open the zip from memory
with zipfile.ZipFile(zip_bytes) as zf:
    # List files inside (optional)
    print("Files inside ZIP:", zf.namelist())

    # 3. Open the CSV inside
    csv_filename = zf.namelist()[0]  # Adjust if needed
    csv_file = zf.open(csv_filename)
    csv_stream = io.TextIOWrapper(csv_file, encoding="latin1")  # Wrap binary as text

    # 4. Connect DuckDB and create a view
    con = duckdb.connect()

    #  Load spatial functions
    con.execute("INSTALL spatial;")
    con.execute("LOAD spatial;")

    # Create a relation from the csv_stream
    rel = con.read_csv(csv_stream, header=True, auto_detect=True)

    # Register it as a view
    rel.create_view("istat_units")

# 5. Run your custom SQL query and export the result
csv_output_path = "IT_countrywide.csv"
query = f"""
COPY (
    SELECT
        st_x(a.geometry) as lon,
        st_y(a.geometry) as lat,
        a.*,
        "Denominazione in italiano" as COMUNE,
        "Denominazione dell'Unità territoriale sovracomunale
(valida a fini statistici)" as PROVINCIA,
        "Denominazione Regione" as REGIONE,
    FROM
        read_parquet('https://github.com/ivandorte/anncsu_dump/raw/refs/heads/main/geodati/INDIR_ITA_20250128_GEO.parquet') a
    JOIN
        istat_units
    ON
        "Codice Comune formato alfanumerico" = CODICE_ISTAT
)
TO '{csv_output_path}';
"""

con.execute(query)

# 6. Zip the CSV
zip_output_path = "IT_countrywide.zip"

with zipfile.ZipFile(zip_output_path, "w", zipfile.ZIP_DEFLATED) as zipf:
    zipf.write(csv_output_path, arcname=os.path.basename(csv_output_path))

# 7. (Optional) Delete the raw CSV after zipping
os.remove(csv_output_path)

print(f"Created zipped CSV: {zip_output_path}")
