#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import lxml.etree as ET
import os.path
import requests
import zipfile
import csv
from urllib import parse

cache_dir = "./cache"
out_path = "./pt_addresses.csv"

base_url = "http://inspire.ine.pt/AD/atom/downloadservice_en.xml"


# Returns the path where a file should be cached
def cache_file_path(url):
    return os.path.join(cache_dir, os.path.basename(url))


# Returns True if we have a valid (i.e. completely downloaded) file already cached. If a file is damaged it is removed.
def file_already_cached(url):
    local_path = cache_file_path(url)

    if not os.path.exists(local_path):
        return False

    file_ok = True
    try:
        with zipfile.ZipFile(local_path, "r") as zip_file:
            file_ok = zip_file.testzip() is None
    except:
        file_ok = False

    if not file_ok:
        os.remove(local_path)

    return file_ok


# Downloads a file to cache
def download_file_to_cache(url, chunk_size):
    response = requests.get(url, stream=True)
    with open(cache_file_path(url), "wb") as cached_file:
        for chunk in response.iter_content(chunk_size=chunk_size):
            cached_file.write(chunk)


ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

base_page = ET.fromstring(requests.get(base_url).content)
base_patterns = (
    "http://inspire.ine.pt/AD/atom/CDG_AD_BNM",
    "https://inspire.ine.pt/AD/atom/CDG_AD_BNM",
)
file_pattern = "EPSG4326.zip"


for nuts_link in base_page.findall(".//atom:entry/atom:link", namespaces=ATOM_NS):
    nuts_url = nuts_link.attrib["href"]
    if nuts_url.startswith(base_patterns):
        print("Caching files from " + nuts_url)
        nuts_page = ET.fromstring(requests.get(nuts_url).content)
        for file_link in nuts_page.findall(
            ".//atom:entry/atom:link", namespaces=ATOM_NS
        ):
            file_url = file_link.attrib["href"]
            if file_url.endswith(file_pattern):
                # This is to fix incorrect links in the atom feed for Madeira
                url_lst = list(parse.urlparse(file_url))
                url_lst[1] = "inspire.ine.pt"
                file_url = parse.urlunparse(url_lst)
                print(file_url)
                if not file_already_cached(file_url):
                    download_file_to_cache(file_url, 512)

print("All files cached, will begin parsing")

with open(out_path, "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = [
        "id",
        "street",
        "house",
        "unit",
        "floor",
        "postcode",
        "city",
        "lon",
        "lat",
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for cached_file in [fi for fi in os.listdir(cache_dir) if fi.endswith(".zip")]:
        print("Parsing " + cached_file)
        postdescriptors = {}
        thoroughfarenames = {}

        with zipfile.ZipFile(cache_file_path(cached_file), "r") as zip_file:
            zip_page = ET.fromstring(zip_file.read(zip_file.namelist()[0]))
            ns = zip_page.nsmap.copy()
            ns.setdefault("wfs", "http://www.opengis.net/wfs/2.0")
            ns.setdefault("ad", "http://inspire.ec.europa.eu/schemas/ad/4.0")
            ns.setdefault("gn", "http://inspire.ec.europa.eu/schemas/gn/4.0")
            ns.setdefault("gml", "http://www.opengis.net/gml/3.2")
            ns.setdefault("xlink", "http://www.w3.org/1999/xlink")

            for pc in zip_page.findall(".//ad:PostalDescriptor", namespaces=ns):
                pc_id = pc.get("{%s}id" % ns["gml"])
                pc_locality_el = pc.find(".//gn:text", namespaces=ns)
                pc_postcode_el = pc.find("ad:postCode", namespaces=ns)
                pc_locality = (
                    pc_locality_el.text if pc_locality_el is not None else None
                )
                pc_postcode = (
                    pc_postcode_el.text if pc_postcode_el is not None else None
                )

                postdescriptors[pc_id] = {
                    "pc_locality": pc_locality,
                    "pc_postcode": pc_postcode,
                }

            for tf in zip_page.findall(".//ad:ThoroughfareName", namespaces=ns):
                tf_id = tf.get("{%s}id" % ns["gml"])
                tf_name_el = tf.find(".//gn:text", namespaces=ns)
                tf_name = tf_name_el.text if tf_name_el is not None else None
                thoroughfarenames[tf_id] = tf_name

            count = 0

            for ad in zip_page.findall(".//ad:Address", namespaces=ns):
                ad_id = ad.get("{%s}id" % ns["gml"])
                pos_el = ad.find(".//gml:pos", namespaces=ns)
                if pos_el is None:
                    continue
                ad_pos = pos_el.text.split()

                ad_num = None
                ad_unit = None
                ad_floor = None
                ad_pc = None
                ad_tf = None

                locator = ad.find(".//ad:AddressLocator", namespaces=ns)
                if locator is not None:
                    for loc in locator.findall(
                        ".//ad:LocatorDesignator", namespaces=ns
                    ):
                        loc_type = loc.find("ad:type", namespaces=ns)
                        loc_des = loc.find("ad:designator", namespaces=ns)
                        if loc_type is None or loc_des is None:
                            continue
                        loc_href = loc_type.get("{%s}href" % ns["xlink"])
                        if (
                            loc_href
                            == "http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/buildingIdentifier"
                        ):
                            ad_num = loc_des.text
                        elif (
                            loc_href
                            == "http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/unitIdentifier"
                        ):
                            ad_unit = loc_des.text
                        elif (
                            loc_href
                            == "http://inspire.ec.europa.eu/codelist/LocatorDesignatorTypeValue/floorIdentifier"
                        ):
                            ad_floor = loc_des.text

                for comp in ad.findall(".//ad:component", namespaces=ns):
                    href = comp.get("{%s}href" % ns["xlink"])
                    if not href:
                        continue
                    comp_ref = href[1:] if href.startswith("#") else href
                    pc_ref = postdescriptors.get(comp_ref)
                    if pc_ref is not None and ad_pc is None:
                        ad_pc = pc_ref
                    tf_ref = thoroughfarenames.get(comp_ref)
                    if tf_ref is not None and ad_tf is None:
                        ad_tf = tf_ref

                count = count + 1
                postcode = ad_pc["pc_postcode"] if ad_pc is not None else None
                city = ad_pc["pc_locality"] if ad_pc is not None else None
                writer.writerow(
                    {
                        "id": ad_id,
                        "street": ad_tf,
                        "house": ad_num,
                        "unit": ad_unit,
                        "floor": ad_floor,
                        "postcode": postcode,
                        "city": city,
                        "lon": ad_pos[1],
                        "lat": ad_pos[0],
                    }
                )

            print("Parsed " + str(count) + " rows")
