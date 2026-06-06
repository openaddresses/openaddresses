from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import xml.etree.ElementTree as ET

import requests

# The Hong Kong Address Dataset is offered through the CSDI portal.
# It's a JS-heavy portal that loads the download link dynamically.
# This script uses the metadata API to retrieve the download URL
# without requiring JavaScript execution. It relies on a JSESSIONID
# to be present in the cookies. This is automated, but may be brittle.

# The DATASET_ID *should* be a stable identifier for the dataset, but this is unconfirmed.
DATASET_ID = "dpo_rcd_1629267205232_33603"
DATASET_PAGE_URL = f"https://portal.csdi.gov.hk/csdi-webpage/dataset/{DATASET_ID}"
METADATA_XML_URL = (
    f"https://portal.csdi.gov.hk/geoportal/rest/metadata/item/{DATASET_ID}/xml"
)
STATIC_DOWNLOAD_HOST = "https://static.csdi.gov.hk"
REQUEST_TIMEOUT = 60
HK_DIR = Path(__file__).resolve().parent.parent
DEFAULT_ARCHIVE_PATH = HK_DIR / "ALS_GeoJSON.zip"
ARCHIVE_GLOB = "ALS_GeoJSON*.zip"
XML_NAMESPACES = {
    "gmd": "http://www.isotc211.org/2005/gmd",
    "gco": "http://www.isotc211.org/2005/gco",
}


class DownloadInstructionsError(RuntimeError):
    """Raised when automatic download fails and the user should download manually."""


def find_local_archive(archive_path: Path = DEFAULT_ARCHIVE_PATH) -> Path | None:
    """Find a locally available archive, accepting any ALS_GeoJSON*.zip variant."""
    if archive_path.exists():
        return archive_path

    matches = sorted(
        archive_path.parent.glob(ARCHIVE_GLOB),
        key=lambda path: (path.name != archive_path.name, path.name),
    )
    return matches[0] if matches else None


def fetch_metadata_xml(session: requests.Session, url: str = METADATA_XML_URL) -> str:
    """Fetch the dataset metadata XML that describes the current downloadable resources."""
    response = session.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.text


def extract_current_download_url(metadata_xml: str) -> str:
    """Extract the current DATA download URL from the dataset metadata XML."""
    root = ET.fromstring(metadata_xml)

    for transfer_option in root.findall(
        ".//gmd:distributionInfo//gmd:transferOptions",
        XML_NAMESPACES,
    ):
        profile = transfer_option.find(
            ".//gmd:applicationProfile/gco:CharacterString",
            XML_NAMESPACES,
        )
        if profile is None or profile.text != "DATA":
            continue

        link = transfer_option.find(
            ".//gmd:linkage/gmd:URL",
            XML_NAMESPACES,
        )
        if link is not None and link.text:
            return link.text

    raise ValueError("Could not find a DATA download URL in the metadata XML.")


def bootstrap_download_session(
    session: requests.Session, dataset_page_url: str = DATASET_PAGE_URL
) -> str:
    """Fetch the dataset page to obtain a fresh JSESSIONID cookie for downloads."""
    response = session.get(dataset_page_url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    session_cookie = session.cookies.get("JSESSIONID")
    if not session_cookie:
        raise ValueError("CSDI dataset page did not return a JSESSIONID cookie.")

    return session_cookie


def convert_to_static_download_url(url: str) -> str:
    """Rewrite the portal download URL onto the static host used by browser downloads."""
    parsed = urlparse(url)
    return f"{STATIC_DOWNLOAD_HOST}{parsed.path}"


def download_archive(session: requests.Session | None = None) -> bytes:
    """Download the current ZIP archive using the CSDI metadata and session flow."""
    managed_session = session or requests.Session()
    metadata_xml = fetch_metadata_xml(managed_session)
    portal_download_url = extract_current_download_url(metadata_xml)
    session_cookie = bootstrap_download_session(managed_session)
    static_download_url = convert_to_static_download_url(portal_download_url)

    response = managed_session.get(
        static_download_url,
        headers={"Cookie": f"JSESSIONID={session_cookie}"},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.content


def build_manual_download_message(
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
    dataset_page_url: str = DATASET_PAGE_URL,
) -> str:
    """Build instructions for downloading the archive manually."""
    return (
        "Automatic download failed.\n"
        f"Download the current ZIP manually from:\n{dataset_page_url}\n"
        f"Then place it in:\n{archive_path.parent}\n"
        f"Accepted filenames include:\n{archive_path.name}\n{ARCHIVE_GLOB}"
    )


def load_or_download_archive(
    archive_path: Path = DEFAULT_ARCHIVE_PATH,
) -> tuple[bytes, str, Path]:
    """Return archive bytes and the archive path used for processing."""
    local_archive = find_local_archive(archive_path)
    if local_archive is not None:
        return local_archive.read_bytes(), f"local ({local_archive.name})", local_archive

    try:
        archive_bytes = download_archive()
    except Exception as exc:
        raise DownloadInstructionsError(
            build_manual_download_message(archive_path)
        ) from exc

    archive_path.write_bytes(archive_bytes)
    return archive_bytes, "downloaded", archive_path
