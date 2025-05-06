#!/usr/bin/env python

import requests
import time
from multiprocessing import Pool
import csv
import os
from tqdm import tqdm  # Add tqdm for progress bar


# The script fetches building data from the OneMap API for Singapore postal codes and saves the results to a CSV file.
# Register at https://www.onemap.gov.sg/apidocs/register for an API key and replace the xxxxxxxxxxxxxxxxxxx with your key.
# If the script times out, replace the 0 in postal_codes = range(0, 1000000) with the latest chunk and resume.


def pcode_to_data(pcode):
    if int(pcode) % 1000 == 0:
        print(f"Processing postal code: {pcode}")

    page = 1
    results = []
    headers = {"Authorization": "Bearer xxxxxxxxxxxxxxxxxxx"}

    while True:
        try:
            response = requests.get(
                "https://www.onemap.gov.sg/api/common/elastic/search?searchVal={0}&returnGeom=Y&getAddrDetails=Y&pageNum={1}".format(
                    pcode, page
                ),
                headers=headers,
            )
            response.raise_for_status()  # Ensure HTTP errors are raised
            data = response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching postal code {pcode}: {e}. Retrying in 2 seconds...")
            time.sleep(2)
            continue

        if "results" in data:
            results.extend(data["results"])
        else:
            print(f"No results found for postal code {pcode}.")
            break

        if data.get("totalNumPages", 0) > page:
            page += 1
        else:
            break

    return results


if __name__ == "__main__":
    pool = Pool(processes=10)

    postal_codes = range(0, 1000000)
    postal_codes = ["{0:06d}".format(p) for p in postal_codes]

    all_buildings = []
    output_file = "sg_countrywide.csv"

    # Check if the file exists to determine write mode
    file_exists = os.path.exists(output_file)

    # Open the CSV file in append mode if it exists, otherwise write mode
    with open(
        output_file, "a" if file_exists else "w", encoding="utf-8", newline=""
    ) as f:
        writer = None

        # Process postal codes in chunks with a progress bar
        for i in tqdm(range(0, len(postal_codes), 10000), desc="Processing chunks"):
            chunk = postal_codes[i : i + 10000]
            print(f"Processing postal codes {chunk[0]} to {chunk[-1]}...")

            # Fetch data for the current chunk
            chunk_results = pool.map(pcode_to_data, chunk)

            # Flatten the list of lists
            flattened_chunk = [
                building for sublist in chunk_results for building in sublist
            ]

            # Check if we have any results
            if not flattened_chunk:
                print(
                    f"Warning: No building data found for postal codes {chunk[0]} to {chunk[-1]}."
                )
                continue

            # Sort the flattened chunk
            flattened_chunk.sort(
                key=lambda b: (b.get("POSTAL", ""), b.get("SEARCHVAL", ""))
            )

            # Write to CSV
            if writer is None:
                writer = csv.DictWriter(f, fieldnames=flattened_chunk[0].keys())
                if not file_exists:  # Write header only if the file is new
                    writer.writeheader()
            writer.writerows(flattened_chunk)

            # Append to the overall results
            all_buildings.extend(flattened_chunk)

        # Close and join the pool after all chunks are processed
        pool.close()  # Close the pool to prevent new tasks from being submitted
        pool.join()  # Wait for all worker processes to finish

    print(f"✅ Output saved to {output_file}")
    print(f"Total buildings: {len(all_buildings)}")
