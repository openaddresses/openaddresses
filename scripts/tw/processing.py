#!/usr/bin/env python3
import re
import pandas as pd
import argparse
import os
import zipfile
from pyproj import Transformer
import chardet


def normalize_areacode(code):
    """Normalize 8-digit codes like 63000010 → 6300100 and pad 6-digit codes to 7 digits"""
    if isinstance(code, str):
        code = code.zfill(7)
        if len(code) == 8 and code[2:4] == "00":
            return code[:2] + code[4:] + "0"
    return code


def normalize_col(name):
    """Strip punctuation and separators for fuzzy column matching (keeps CJK, Latin, digits)."""
    return re.sub(r'[^a-zA-Z0-9一-鿿]', '', name)


def fallback_transform(code):
    # Re-inserts "00" at position 2 for unmatched 7-char codes, reversing normalize_areacode
    if isinstance(code, str) and len(code) == 7:
        return code[:2] + "00" + code[2:-2]
    return code


def load_address_csv(filepath):
    """Detect encoding and load address CSV with fallbacks."""
    with open(filepath, "rb") as f:
        raw_data = f.read(100000)
        detected = chardet.detect(raw_data)
        encoding = detected["encoding"]
        confidence = detected["confidence"]

    print(f"🔍 Detected encoding: {encoding} (confidence: {confidence:.2f})")

    candidates = [encoding, "utf-8", "big5", "big5hkscs", "cp950", "latin1"]
    seen = set()
    for enc in [e for e in candidates if e and e.lower() not in seen and not seen.add(e.lower())]:
        try:
            df = pd.read_csv(filepath, dtype=str, encoding=enc)
            print(f"✅ Successfully decoded using: {enc}")
            return df
        except UnicodeDecodeError:
            print(f"⚠️  Failed to decode with encoding '{enc}', trying next...")

    # Last resort: replace undecodable characters
    print("⚠️  All decode attempts failed. Using 'utf-8' with errors='replace'")
    return pd.read_csv(filepath, dtype=str, encoding="utf-8", errors="replace")


def main(address_csv, output_csv, code_table_csv, reproject, source_crs="EPSG:3826"):
    address_df = load_address_csv(address_csv)

    # Normalize English column variants. Keys are normalize_col().lower() forms so that
    # camelCase, leading spaces, and punctuation all collapse to the same lookup key.
    english_to_chinese = {
        "countycode": "省市縣市代碼",
        "citycode": "省市縣市代碼",
        "areacode": "鄉鎮市區代碼",
        "districtcode": "鄉鎮市區代碼",
        "village": "村里",
        "neighbor": "鄰",
        "neighborhood": "鄰",
        "streetroadsection": "街路段",
        "area": "地區",
        "lane": "巷",
        "alley": "弄",
        "number": "號",
        "housenumber": "號",
        "coordinatex": "橫座標",
        "coordinatey": "縱座標",
    }

    renamed_cols = {}
    for col in address_df.columns:
        key = normalize_col(col).lower()
        if key in english_to_chinese:
            renamed_cols[col] = english_to_chinese[key]

    if renamed_cols:
        print(f"🔁 Renaming English column headers: {renamed_cols}")
        address_df.rename(columns=renamed_cols, inplace=True)

    # Punctuation variants (街_路段, 街（路段）, etc.) are caught by normalize_col.
    # Word-separator variants that survive normalization need an explicit entry.
    alias_map = {
        "TWD97橫坐標": "橫座標",
        "TWD97縱坐標": "縱座標",
        "WGS84經度": "x_4326",
        "WGS84緯度": "y_4326",
        "街路段": "街路段",
        "街或路段": "街路段",
    }
    norm_to_dest = {normalize_col(src): dest for src, dest in alias_map.items()}
    col_renames = {}
    for col in address_df.columns:
        norm = normalize_col(col)
        if norm in norm_to_dest:
            dest = norm_to_dest[norm]
            if dest not in address_df.columns and dest not in col_renames.values():
                col_renames[col] = dest
    if col_renames:
        address_df.rename(columns=col_renames, inplace=True)

    if "地區" not in address_df.columns:
        print("⚠️  '地區' column is missing from input. Filling with null values.")
        address_df["地區"] = pd.NA

    has_code_columns = (
        "省市縣市代碼" in address_df.columns and "鄉鎮市區代碼" in address_df.columns
    )

    if not has_code_columns:
        if "縣市" in address_df.columns and "鄉鎮市區" in address_df.columns:
            print("ℹ️  Using '縣市'/'鄉鎮市區' columns for county/town; skipping code join.")
            address_df["county"] = address_df["縣市"]
            address_df["town"] = address_df["鄉鎮市區"]
            address_df["省市縣市代碼"] = pd.NA
            address_df["鄉鎮市區代碼"] = pd.NA
        else:
            raise KeyError("Missing required code columns or county/town name columns.")
    elif (
        not address_df["省市縣市代碼"].str.isnumeric().all()
        or not address_df["鄉鎮市區代碼"].str.isnumeric().all()
    ):
        print(
            "⚠️  Non-numeric values detected in '省市縣市代碼' or '鄉鎮市區代碼'. Skipping join — using them directly for 'county' and 'town'."
        )
        address_df["county"] = address_df["省市縣市代碼"]
        address_df["town"] = address_df["鄉鎮市區代碼"]
    else:
        address_df["省市縣市代碼"] = address_df["省市縣市代碼"].str.zfill(5)
        address_df["鄉鎮市區代碼"] = address_df["鄉鎮市區代碼"].apply(normalize_areacode)

        code_df = (
            pd.read_csv(code_table_csv, dtype=str)
            .rename(columns={"區里代碼": "鄉鎮市區代碼"})
            .drop_duplicates(subset=["鄉鎮市區代碼"], keep="first")
        )

        merged_df = pd.merge(
            address_df, code_df, on="鄉鎮市區代碼", how="left", indicator=True
        )
        total_rows = len(merged_df)
        unmatched_mask = (merged_df["_merge"] != "both").values
        num_unmatched = unmatched_mask.sum()

        if num_unmatched > 0:
            print(
                f"⚠️  {num_unmatched} out of {total_rows} rows did not join initially. Attempting fallback transformation..."
            )
            address_df.loc[unmatched_mask, "鄉鎮市區代碼"] = address_df.loc[
                unmatched_mask, "鄉鎮市區代碼"
            ].apply(fallback_transform)
            merged_df = pd.merge(
                address_df, code_df, on="鄉鎮市區代碼", how="left", indicator=True
            )
            recovered = num_unmatched - (merged_df["_merge"] != "both").values.sum()
            if recovered > 0:
                print(f"✅ Fallback transformation matched {recovered} previously unmatched rows.")
            else:
                print("⚠️  Fallback transformation did not recover any rows.")

        final_unmatched = (merged_df["_merge"] != "both").sum()
        if final_unmatched == 0:
            print(f"✅ All {total_rows} rows successfully joined.")
        else:
            print(f"⚠️  {final_unmatched} rows still failed to join after fallback.")

        address_df["county"] = merged_df["縣市名稱"].values
        address_df["town"] = merged_df["區鄉鎮名稱"].values

    if not reproject:
        print("🚫 Skipping reprojection. Copying original coords to x_4326/y_4326.")
        if "x_4326" not in address_df.columns:
            address_df["x_4326"] = address_df["橫座標"]
        if "y_4326" not in address_df.columns:
            address_df["y_4326"] = address_df["縱座標"]
        address_df["x_3826"] = pd.NA
        address_df["y_3826"] = pd.NA
    else:
        print(f"🔄 Reprojecting coordinates from {source_crs} to EPSG:4326...")
        if "x_3826" not in address_df.columns:
            address_df["x_3826"] = address_df["橫座標"]
        if "y_3826" not in address_df.columns:
            address_df["y_3826"] = address_df["縱座標"]

        if "x_4326" in address_df.columns and "y_4326" in address_df.columns:
            print("✅ Using provided WGS84 coordinates.")
        else:
            transformer = Transformer.from_crs(source_crs, "EPSG:4326", always_xy=True)
            valid = (
                pd.to_numeric(address_df["x_3826"], errors="coerce").notna()
                & pd.to_numeric(address_df["y_3826"], errors="coerce").notna()
            )
            address_df["x_4326"] = pd.NA
            address_df["y_4326"] = pd.NA
            lons, lats = transformer.transform(
                address_df.loc[valid, "x_3826"].astype(float).values,
                address_df.loc[valid, "y_3826"].astype(float).values,
            )
            address_df.loc[valid, "x_4326"] = lons
            address_df.loc[valid, "y_4326"] = lats

    column_pairs = [
        ("省市縣市代碼", "countycode"),
        ("鄉鎮市區代碼", "areacode"),
        ("村里", "village"),
        ("鄰", "neighbor"),
        ("街路段", "street"),
        ("地區", "area"),
        ("巷", "lane"),
        ("弄", "alley"),
        ("號", "number"),
        ("x_3826", "x_3826"),
        ("y_3826", "y_3826"),
        ("x_4326", "x_4326"),
        ("y_4326", "y_4326"),
        ("county", "county"),
        ("town", "town"),
    ]
    address_df = address_df[[col for col, _ in column_pairs]]
    address_df.rename(columns=dict(column_pairs), inplace=True)

    address_df.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"📄 CSV saved to: {output_csv}")

    zip_filename = os.path.splitext(output_csv)[0] + ".zip"
    with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write(output_csv, arcname=os.path.basename(output_csv))
    print(f"🗜️  Zipped output to: {zip_filename}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Join Taiwan address CSV with district codes."
    )
    parser.add_argument("address_csv", help="Path to the address CSV file")
    parser.add_argument("output_csv", help="Path to save the output CSV file")
    parser.add_argument(
        "--code_table",
        default=os.path.join(os.path.dirname(__file__), "Taiwan_county_district_codes.csv"),
        help="Optional path to county/district code table (default: ./Taiwan_county_district_codes.csv)",
    )
    parser.add_argument(
        "--no-reproject",
        action="store_true",
        help="Skip coordinate reprojection and copy original values into x_4326/y_4326",
    )
    parser.add_argument(
        "--source-crs",
        default="EPSG:3826",
        help="Source CRS of the input coordinates (default: EPSG:3826). "
             "Use EPSG:3825 for outlying islands (Penghu, Kinmen, Matsu).",
    )
    args = parser.parse_args()

    if not os.path.exists(args.code_table):
        raise FileNotFoundError(
            f"County/district code table not found at: {args.code_table}"
        )

    main(args.address_csv, args.output_csv, args.code_table, not args.no_reproject, args.source_crs)
