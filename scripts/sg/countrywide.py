#!/usr/bin/env python

import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import csv
import os
from tqdm import tqdm


# Register at https://www.onemap.gov.sg/apidocs/register for an API key.
# If the script times out, replace the start value in range(0, 1000000) and resume.

TOKEN = "Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjo3MDQ3LCJmb3JldmVyIjpmYWxzZSwiaXNzIjoiT25lTWFwIiwiaWF0IjoxNzgwNTIwODk2LCJuYmYiOjE3ODA1MjA4OTYsImV4cCI6MTc4MDc4MDA5NiwianRpIjoiZWRiM2RiMzItNmQ1NS00Y2FmLWEyOTQtNWI4MTAwOWJkZGMyIn0.tNHuyXLCtn4LcJuri42C7tbR6rzTacWVaY_kI80ewh-jkh3uQ0brV2fP2YopivTpqdc3qR4orostxZU0lG_p6dyr_QMYNdnkZCq4RWMiAtY0Xwr4SZTmAQg3_NGC30oXMZQsuf3-V_LK_6HcQeIf1FeQzH3Ygq9Q_BP1kKWcPEYRge7AgMqZ-NeQ1F8kNFfZYTRB5q3lUwK6bcN4enWnxYtcLKrZ6bgMcbREsu7u3laem8B2t9bn0Roqxfo7Cn80iKxLyn59fUUyDkMoLwvh_CvwtEbKMZzOy0zj4ix0hQvU2u7VU4UiMugsIE-0iCETOlSn9mJa8LDkNXpDiE4bSQw"
WORKERS = 50

thread_local = threading.local()


def get_session():
    if not hasattr(thread_local, "session"):
        s = requests.Session()
        s.headers["Authorization"] = TOKEN
        thread_local.session = s
    return thread_local.session


def pcode_to_data(pcode):
    if int(pcode) % 10000 == 0:
        print(f"Processing postal code: {pcode}")

    session = get_session()
    page = 1
    results = []

    while True:
        data = None
        for attempt in range(5):
            try:
                response = session.get(
                    "https://www.onemap.gov.sg/api/common/elastic/search",
                    params={
                        "searchVal": pcode,
                        "returnGeom": "Y",
                        "getAddrDetails": "Y",
                        "pageNum": page,
                    },
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()
                break
            except requests.exceptions.RequestException as e:
                wait = 2 ** attempt
                print(f"Attempt {attempt + 1}/5 failed for {pcode}: {e}. Retrying in {wait}s...")
                time.sleep(wait)

        if data is None:
            print(f"Giving up on postal code {pcode} after 5 attempts.")
            break

        if "results" in data:
            results.extend(data["results"])
        else:
            break

        if data.get("totalNumPages", 0) > page:
            page += 1
        else:
            break

    return results


if __name__ == "__main__":
    postal_codes = ["{0:06d}".format(p) for p in range(1, 1000000)]

    output_file = "sg_countrywide.csv"
    file_exists = os.path.exists(output_file)
    total_buildings = 0

    with open(output_file, "a" if file_exists else "w", encoding="utf-8", newline="") as f:
        writer = None

        with ThreadPoolExecutor(max_workers=WORKERS) as executor:
            for i in tqdm(range(0, len(postal_codes), 10000), desc="Processing chunks"):
                chunk = postal_codes[i : i + 10000]
                print(f"Processing postal codes {chunk[0]} to {chunk[-1]}...")

                chunk_results = list(executor.map(pcode_to_data, chunk))
                flattened = [b for sublist in chunk_results for b in sublist]

                if not flattened:
                    print(f"Warning: No building data found for postal codes {chunk[0]} to {chunk[-1]}.")
                    continue

                flattened.sort(key=lambda b: (b.get("POSTAL", ""), b.get("SEARCHVAL", "")))

                if writer is None:
                    writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
                    if not file_exists:
                        writer.writeheader()
                writer.writerows(flattened)
                total_buildings += len(flattened)

    print(f"✅ Output saved to {output_file}")
    print(f"Total buildings: {total_buildings}")
