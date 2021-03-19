#!/usr/bin/env python

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import pandas as pd
import requests
from tqdm import tqdm


def get_onemap_data(postcode):
    results = []
    page = 1
    url_format = "https://developers.onemap.sg/commonapi/search?searchVal={postcode}&returnGeom=Y&getAddrDetails=Y&pageNum={page}"

    while True:
        try:
            response = requests.get(url_format.format(postcode=postcode, page=page)).json()
        except requests.exceptions.ConnectionError:
            print(f"Fetching {postcode} failed. Retrying in 2 sec")
            time.sleep(2)
            continue

        results.extend(response["results"])
        if page >= response["totalNumPages"]:
            break
        page = page + 1

    return results


def generate_postcodes(txt_path="sg.txt"):
    completed = set()
    try:
        with open(txt_path) as f:
            completed.update(f.read().splitlines())
    except FileNotFoundError:
        pass

    postal_codes = set(f"{p:06d}" for p in range(0, 1000000))
    postal_codes = postal_codes - completed
    return postal_codes


def jsonlines_to_geojson(json_path="sg.json", csv_path="sg.csv", geojson_path="sg.geojson"):
    dtype = {
        "BLK_NO": "str",
        "ROAD_NAME": "str",
        "BUILDING": "str",
        "ADDRESS": "str",
        "POSTAL": "str",
        "X": "float",
        "Y": "float",
        "LATITUDE": "float",
        "LONGITUDE": "float",
    }
    df = (
        pd.read_json(json_path, dtype=dtype, lines=True)[dtype.keys()]
            .replace("NIL", "")
            .sort_values(["POSTAL", "BUILDING"], ignore_index=False)
            .drop_duplicates(ignore_index=False)
    )
    df.to_csv(csv_path, index=False)
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df["LATITUDE"], df["LONGITUDE"]))
    gdf.to_file(geojson_path, driver="GeoJSON")
    return gdf


if __name__ == "__main__":
    fname = "sg"
    txt_path = f"{fname}.txt"
    json_path = f"{fname}.json"
    csv_path = f"{fname}.csv"
    geojson_path = f"{fname}.geojson"

    postal_codes = generate_postcodes(txt_path)

    with tqdm(postal_codes) as pbar, \
            open(json_path, "a") as f_json, \
            open(txt_path, "a") as f_txt, \
            ThreadPoolExecutor() as executor:

        futures_args = {
            executor.submit(get_onemap_data, postcode): postcode
            for postcode in postal_codes
        }

        for future in as_completed(futures_args):
            postcode = futures_args[future]
            results = future.result()

            if results:
                f_json.write("\n".join(json.dumps(entry) for entry in results))
                f_json.write("\n")
            f_txt.write(postcode)
            f_txt.write("\n")
            pbar.update()

    jsonlines_to_geojson(json_path, csv_path, geojson_path)
