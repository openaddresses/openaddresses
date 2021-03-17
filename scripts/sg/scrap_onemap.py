#!/usr/bin/env python

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import geopandas as gpd
import pandas as pd
import requests
from tqdm import tqdm


def get_onemap_data(pcode):
    results = []
    page = 1
    url_format = "https://developers.onemap.sg/commonapi/search?searchVal={pcode}&returnGeom=Y&getAddrDetails=Y&pageNum={page}"

    while True:
        try:
            response = requests.get(url_format.format(pcode=pcode, page=page)).json()
        except requests.exceptions.ConnectionError:
            print(f"Fetching {pcode} failed. Retrying in 2 sec")
            time.sleep(2)
            continue

        results.extend(response["results"])
        if page >= response["totalNumPages"]:
            break
        page = page + 1

    return pcode, results


def generate_postcodes(txt_path="sg.txt"):
    completed = set()
    try:
        with open(txt_path) as f:
            completed.update(f.read().splitlines())
    except FileNotFoundError:
        pass

    postal_codes = set(f"{p:06d}" for p in range(0, 1000000))
    postal_codes = sorted(postal_codes - completed)
    return postal_codes


def json_to_geojson(json_path="sg.json", csv_path="sg.csv", geojson_path="sg.geojson"):
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
    df = pd.read_json(json_path, dtype=dtype, lines=True)[dtype.keys()].sort_values(["POSTAL", "BUILDING"])
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

        futures = [executor.submit(get_onemap_data, pcode) for pcode in postal_codes]

        for future in as_completed(futures):
            pcode, result = future.result()

            for entry in result:
                f_json.write(json.dumps(entry))
                f_json.write("\n")
            f_txt.write(pcode)
            f_txt.write("\n")
            pbar.update(1)

    json_to_geojson(json_path, csv_path, geojson_path)
