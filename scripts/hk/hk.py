import requests
import zipfile
import io
import os
import json
import pandas as pd

# URL of the ZIP file. This may need to be updated for new versions.
# Location of data is https://portal.csdi.gov.hk/geoportal/#metadataInfoPanel
zip_url = "https://p1static.csdi.gov.hk/csdi-webpage/download/open/629ea2e16bea32539fe5e5d9998f88fc9dd9cdec7c777c2ac0142393a7f73ba1"

# Directory to extract files
extract_dir = "geojson_files"
os.makedirs(extract_dir, exist_ok=True)

# Download and extract the ZIP file
response = requests.get(zip_url)
if response.status_code == 200:
    with zipfile.ZipFile(io.BytesIO(response.content)) as z:
        z.extractall(extract_dir)
else:
    print("Failed to download the file.")
    exit()

# List all geojson files, excluding the unwanted one
excluded_file = "als_addresses_3d_(public_rental_housing).geojson"
geojson_files = [
    f for f in os.listdir(extract_dir) if f.endswith(".geojson") and f != excluded_file
]

data_list = []


def flatten_dict(d, parent_key="", sep="_"):
    """Recursively flattens a nested dictionary with custom prefixes."""
    items = []
    for k, v in d.items():
        prefix = ""
        if "ChiPremisesAddress" in parent_key or "ChiVillage" in parent_key:
            prefix = "ch_"
        elif "EngPremisesAddress" in parent_key or "EngVillage" in parent_key:
            prefix = "en_"
        new_key = f"{prefix}{k}" if prefix else k

        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


# Process each geojson file
for file in geojson_files:
    file_path = os.path.join(extract_dir, file)
    with open(file_path, "r", encoding="utf-8") as f:
        geojson_data = json.load(f)

        for feature in geojson_data.get("features", []):
            properties = feature.get("properties", {})
            geometry = feature.get("geometry", {})
            coordinates = geometry.get("coordinates", [])

            # Flatten nested properties
            flat_properties = flatten_dict(properties)

            # Add geometry data
            flat_properties["longitude"] = (
                coordinates[0] if len(coordinates) > 0 else None
            )
            flat_properties["latitude"] = (
                coordinates[1] if len(coordinates) > 1 else None
            )

            data_list.append(flat_properties)

# Convert to DataFrame and save as CSV
csv_filename = "hk_countrywide.csv"
if data_list:
    df = pd.DataFrame(data_list)
    df.to_csv(csv_filename, index=False, encoding="utf-8-sig")
    print(f"CSV file has been saved as {csv_filename}")

    # Zip the CSV file
    zip_filename = "hk_countrywide.zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(csv_filename)
    print(f"Zipped file has been saved as {zip_filename}")
else:
    print("No valid data found in GeoJSON files.")
