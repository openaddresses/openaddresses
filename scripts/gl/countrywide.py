import requests
import pandas as pd
import geopandas as gpd
import os
import zipfile

# === CONFIGURATION ===
SERVICE_URL = "https://kort.nunagis.gl/refserver/rest/services/Grunddataregistre/Adresseregister_offentlig/MapServer"
BASE_LAYER_ID = 0
JOIN_LAYERS = {
    1: {"join_field": "Vejkode", "return_field": "Vejnavn"},
    4: {
        "join_field": "KommuneKode",
        "return_field": "Kommunenavn",
    },
    3: {
        "join_field": "Lokalitetskode",
        "return_field": "Lokalitetsnavn",
    },
}
OUT_FIELDS = "*"
OUTPUT_CSV = "gl_countrywide.csv"
PAGE_LIMIT = 1000


# === Helper Functions ===
def fetch_data(layer_id, out_fields=OUT_FIELDS):
    """Fetch all features from a layer with pagination, including SHAPE data."""
    url = f"{SERVICE_URL}/{layer_id}/query"
    all_features = []
    offset = 0

    while True:
        params = {
            "where": "1=1",
            "outFields": out_fields,
            "f": "json",
            "returnGeometry": "true",  # Ensure geometry (SHAPE) is included
            "resultOffset": offset,
            "resultRecordCount": PAGE_LIMIT,
        }
        r = requests.get(url, params=params)
        r.raise_for_status()
        response = r.json()
        features = response.get("features", [])
        if not features:
            break
        all_features.extend(features)
        offset += PAGE_LIMIT

    return pd.DataFrame([f["attributes"] for f in all_features]), all_features


def fetch_join_data(layer_id, join_fields, return_field):
    """Fetch join data from a layer with pagination."""
    out_fields = ",".join(join_fields + [return_field])
    df, _ = fetch_data(layer_id, out_fields=out_fields)
    print(f"Join data columns for layer {layer_id}: {df.columns.tolist()}")
    return df


def extract_geometry(features):
    """Extract geometry from the SHAPE column and convert to x, y columns."""
    x_coords = []
    y_coords = []
    for feature in features:
        geometry = feature.get("geometry", {})
        x_coords.append(geometry.get("x"))
        y_coords.append(geometry.get("y"))
    return x_coords, y_coords


# === Main Script ===
if __name__ == "__main__":
    # Step 1: Fetch base layer data
    print("Fetching base layer data...")
    base_df, base_features = fetch_data(BASE_LAYER_ID)
    print(f"Base data columns: {base_df.columns.tolist()}")

    # Step 2: Extract geometry from SHAPE column and add x, y columns
    print("Extracting geometry from SHAPE column...")
    x_coords, y_coords = extract_geometry(base_features)
    base_df["x"] = x_coords
    base_df["y"] = y_coords

    # Step 3: Perform joins with other layers
    for layer_id, join_info in JOIN_LAYERS.items():
        print(f"Joining with layer {layer_id} on {join_info['join_field']}...")

        # Handle special case for layer 1
        if layer_id == 1:
            print("Layer 1 requires joining on both Vejkode and KommuneKode...")
            join_df = fetch_join_data(
                layer_id, ["Vejkode", "Kommunekode"], join_info["return_field"]
            )
            # Rename Kommunekode to KommuneKode for consistency
            if "Kommunekode" in join_df.columns:
                print("Renaming Kommunekode to KommuneKode for merge...")
                join_df = join_df.rename(columns={"Kommunekode": "KommuneKode"})
            # Drop duplicates to ensure one-to-one join
            join_df = join_df.drop_duplicates(subset=["Vejkode", "KommuneKode"])
            base_df = base_df.merge(
                join_df,
                left_on=["Vejkode", "KommuneKode"],
                right_on=["Vejkode", "KommuneKode"],
                how="left",
            )
        else:
            join_df = fetch_join_data(
                layer_id, [join_info["join_field"]], join_info["return_field"]
            )
            if join_df.empty:
                print(f"No data returned for layer {layer_id}, skipping join...")
                continue

            print(f"Before merge - looking for '{join_info['join_field']}' in join_df")
            print(f"Base columns: {base_df.columns.tolist()}")
            print(f"Join columns: {join_df.columns.tolist()}")

            # Create a mapping of the original column name to the join field name
            if (
                join_info["join_field"] == "Lokalitetskode"
                and "LokalitetsKode" in base_df.columns
            ):
                print("Renaming LokalitetsKode to Lokalitetskode for merge")
                base_df = base_df.rename(columns={"LokalitetsKode": "Lokalitetskode"})
            elif (
                join_info["join_field"] == "KommuneKode"
                and "Kommunekode" in join_df.columns
            ):
                print("Renaming Kommunekode to KommuneKode for merge")
                join_df = join_df.rename(columns={"Kommunekode": "KommuneKode"})

            base_df = base_df.merge(
                join_df,
                left_on=join_info["join_field"],
                right_on=join_info["join_field"],
                how="left",
            )

    # Step 4: Save as CSV
    print(f"Saving output to {OUTPUT_CSV}...")
    base_df.to_csv(OUTPUT_CSV, index=False)

    # Step 5: Zip the CSV file
    zip_output = f"{OUTPUT_CSV}.zip"
    print(f"Zipping output to {zip_output}...")
    with zipfile.ZipFile(zip_output, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(OUTPUT_CSV, arcname=os.path.basename(OUTPUT_CSV))
    print("✅ Zipping complete!")

    # Optional: Remove the original CSV file after zipping
    os.remove(OUTPUT_CSV)
    print(f"Removed original CSV file: {OUTPUT_CSV}")
    print("✅ Done!")
