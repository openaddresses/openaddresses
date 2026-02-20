#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
WORK_DIR=${WORK_DIR:-"${ROOT_DIR}/tmp-bag-light"}
URL="https://service.pdok.nl/lv/bag/atom/downloads/bag-light.gpkg"
GPKG_PATH="${WORK_DIR}/bag-light.gpkg"
CSV_PATH="${WORK_DIR}/verblijfsobject.csv"
ZIP_PATH="${WORK_DIR}/verblijfsobject.csv.zip"

if ! command -v ogr2ogr >/dev/null 2>&1; then
  echo "ogr2ogr is required (GDAL)." >&2
  exit 1
fi

mkdir -p "${WORK_DIR}"

if [ ! -f "${GPKG_PATH}" ]; then
  if command -v curl >/dev/null 2>&1; then
    curl -L "${URL}" -o "${GPKG_PATH}"
  elif command -v wget >/dev/null 2>&1; then
    wget -O "${GPKG_PATH}" "${URL}"
  else
    echo "curl or wget is required to download ${URL}." >&2
    exit 1
  fi
fi

rm -f "${CSV_PATH}" "${ZIP_PATH}"

# Export verblijfsobject to CSV with X/Y (lon/lat) columns.
ogr2ogr \
  -f CSV "${CSV_PATH}" "${GPKG_PATH}" verblijfsobject \
  -t_srs EPSG:4326 \
  -lco GEOMETRY=AS_XY

(
  cd "${WORK_DIR}"
  zip -9 "$(basename "${ZIP_PATH}")" "$(basename "${CSV_PATH}")"
)

echo "Wrote ${ZIP_PATH}"
