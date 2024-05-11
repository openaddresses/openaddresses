"""
Build a combined CSV of the Statistics Canada National Address Register
https://www150.statcan.gc.ca/n1/pub/46-26-0002/462600022022001-eng.htm

The data is distributed in two sets of files, addresses and locations. Both have a field
called LOC_GUID that can be used to join the two to attach latitude and longitude to the
addresses.

This script reads all CSVs for both the Addresses and Locations, joins them on the LOC_GUID,
and saves out the addresses with new fields REPPOINT_LATITUDE and REPPOINT_LONGITUDE leaving
all other address fields in place. It also converts to UTF8 in the process from ISO-8859-1.

This assumes you've downloaded the data from the path above and are running it in the unzipped
directory.
"""
import glob
import logging
import zipfile

import pandas as pd


logging.basicConfig(level=logging.INFO)


def read_csvs(z, prefix, **kwargs):
    """
    Read csvs from a zipfile.ZipFile

    Only read files that are in directories like prefix/filename.csv. Skip
    others

    """
    dfs = []
    for info in z.filelist:
        path = info.filename.split("/")
        if len(path) != 2 or path[0] != prefix or not path[1].endswith(".csv"):
            continue
        logging.info(f"Loading {info.filename}")
        with z.open(info.filename) as f:
            dfs.append(pd.read_csv(f, encoding="ISO-8859-1", **kwargs))
    return pd.concat(dfs)


def main():
    with zipfile.ZipFile("2023.zip") as z:
        logging.info("Loading addresses")
        addresses = read_csvs(z, "Addresses")

        logging.info("Loading locations")
        locations = read_csvs(z, "Locations", usecols=["LOC_GUID", "REPPOINT_LATITUDE", "REPPOINT_LONGITUDE"])

    logging.info("Merging addresses and locations")
    combined = pd.merge(addresses, locations, on="LOC_GUID", how="inner")

    logging.info("Saving to canada-nar-combined.csv")
    combined.to_csv("canada-nar-combined.csv", index=False, encoding="UTF-8")


if __name__ == "__main__":
    main()