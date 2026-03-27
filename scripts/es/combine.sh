#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: ./combine.sh /path/to/Spain [/path/to/output.csv.zip]

Combines all CartoCiudad Spain packages into a single zipped CSV containing
only the address points (layer: portalpk_publi). The input directory must
contain all expected province/region zip files.
EOF
}

if [[ $# -lt 1 || $# -gt 2 ]]; then
  usage
  exit 2
fi

input_dir="$1"
if [[ ! -d "$input_dir" ]]; then
  echo "Input directory not found: $input_dir" >&2
  exit 1
fi

if ! command -v ogr2ogr >/dev/null 2>&1; then
  echo "Missing dependency: ogr2ogr (GDAL)." >&2
  exit 1
fi

if ! command -v ogrinfo >/dev/null 2>&1; then
  echo "Missing dependency: ogrinfo (GDAL)." >&2
  exit 1
fi

if ! command -v unzip >/dev/null 2>&1; then
  echo "Missing dependency: unzip." >&2
  exit 1
fi
if ! command -v zip >/dev/null 2>&1; then
  echo "Missing dependency: zip." >&2
  exit 1
fi

input_dir="$(cd "$input_dir" && pwd)"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
output_zip="${2:-$script_dir/es_addresses.csv.zip}"

expected_zips=(
  "CARTOCIUDAD_CALLEJERO_ALAVA.zip"
  "CARTOCIUDAD_CALLEJERO_ALBACETE.zip"
  "CARTOCIUDAD_CALLEJERO_ALICANTE.zip"
  "CARTOCIUDAD_CALLEJERO_ALMERIA.zip"
  "CARTOCIUDAD_CALLEJERO_ASTURIAS.zip"
  "CARTOCIUDAD_CALLEJERO_AVILA.zip"
  "CARTOCIUDAD_CALLEJERO_A_CORUNA.zip"
  "CARTOCIUDAD_CALLEJERO_BADAJOZ.zip"
  "CARTOCIUDAD_CALLEJERO_BALEARES.zip"
  "CARTOCIUDAD_CALLEJERO_BARCELONA.zip"
  "CARTOCIUDAD_CALLEJERO_BURGOS.zip"
  "CARTOCIUDAD_CALLEJERO_CACERES.zip"
  "CARTOCIUDAD_CALLEJERO_CADIZ.zip"
  "CARTOCIUDAD_CALLEJERO_CANTABRIA.zip"
  "CARTOCIUDAD_CALLEJERO_CASTELLON.zip"
  "CARTOCIUDAD_CALLEJERO_CEUTA.zip"
  "CARTOCIUDAD_CALLEJERO_CIUDAD_REAL.zip"
  "CARTOCIUDAD_CALLEJERO_CORDOBA.zip"
  "CARTOCIUDAD_CALLEJERO_CUENCA.zip"
  "CARTOCIUDAD_CALLEJERO_GIRONA.zip"
  "CARTOCIUDAD_CALLEJERO_GRANADA.zip"
  "CARTOCIUDAD_CALLEJERO_GUADALAJARA.zip"
  "CARTOCIUDAD_CALLEJERO_GUIPUZCOA.zip"
  "CARTOCIUDAD_CALLEJERO_HUELVA.zip"
  "CARTOCIUDAD_CALLEJERO_HUESCA.zip"
  "CARTOCIUDAD_CALLEJERO_JAEN.zip"
  "CARTOCIUDAD_CALLEJERO_LAS_PALMAS.zip"
  "CARTOCIUDAD_CALLEJERO_LA_RIOJA.zip"
  "CARTOCIUDAD_CALLEJERO_LEON.zip"
  "CARTOCIUDAD_CALLEJERO_LLEIDA.zip"
  "CARTOCIUDAD_CALLEJERO_LUGO.zip"
  "CARTOCIUDAD_CALLEJERO_MADRID.zip"
  "CARTOCIUDAD_CALLEJERO_MALAGA.zip"
  "CARTOCIUDAD_CALLEJERO_MELILLA.zip"
  "CARTOCIUDAD_CALLEJERO_MURCIA.zip"
  "CARTOCIUDAD_CALLEJERO_NAVARRA.zip"
  "CARTOCIUDAD_CALLEJERO_OURENSE.zip"
  "CARTOCIUDAD_CALLEJERO_PALENCIA.zip"
  "CARTOCIUDAD_CALLEJERO_PONTEVEDRA.zip"
  "CARTOCIUDAD_CALLEJERO_SALAMANCA.zip"
  "CARTOCIUDAD_CALLEJERO_SEGOVIA.zip"
  "CARTOCIUDAD_CALLEJERO_SEVILLA.zip"
  "CARTOCIUDAD_CALLEJERO_SORIA.zip"
  "CARTOCIUDAD_CALLEJERO_TARRAGONA.zip"
  "CARTOCIUDAD_CALLEJERO_TENERIFE.zip"
  "CARTOCIUDAD_CALLEJERO_TERUEL.zip"
  "CARTOCIUDAD_CALLEJERO_TOLEDO.zip"
  "CARTOCIUDAD_CALLEJERO_VALENCIA.zip"
  "CARTOCIUDAD_CALLEJERO_VALLADOLID.zip"
  "CARTOCIUDAD_CALLEJERO_VIZCAYA.zip"
  "CARTOCIUDAD_CALLEJERO_ZAMORA.zip"
  "CARTOCIUDAD_CALLEJERO_ZARAGOZA.zip"
)

missing=()
for zip_name in "${expected_zips[@]}"; do
  if [[ ! -f "$input_dir/$zip_name" ]]; then
    missing+=("$zip_name")
  fi
done

if (( ${#missing[@]} > 0 )); then
  echo "Missing packages in $input_dir:" >&2
  for name in "${missing[@]}"; do
    echo "  - $name" >&2
  done
  exit 1
fi

tmp_dir="$(mktemp -d)"
cleanup() {
  rm -rf "$tmp_dir"
}
trap cleanup EXIT

output_csv="$tmp_dir/es_addresses.csv"
rm -f "$output_csv"

first=1
for zip_name in "${expected_zips[@]}"; do
  zip_path="$input_dir/$zip_name"
  list_file="$tmp_dir/${zip_name%.zip}.contents"
  if ! unzip -Z1 "$zip_path" > "$list_file" 2>"$tmp_dir/unzip.err"; then
    echo "Failed to read zip (corrupt or incomplete): $zip_name" >&2
    cat "$tmp_dir/unzip.err" >&2
    exit 1
  fi
  gpkg_rel="$(grep -E '\.gpkg$' "$list_file" | head -n 1 || true)"
  if [[ -z "$gpkg_rel" ]]; then
    echo "No .gpkg found in $zip_name" >&2
    exit 1
  fi

  src="/vsizip/${zip_path}/${gpkg_rel}"
  if ! ogrinfo -ro -so "$src" portalpk_publi >/dev/null 2>&1; then
    echo "Layer portalpk_publi not found in $zip_name ($gpkg_rel)" >&2
    exit 1
  fi

  echo "Appending $zip_name..."
  tmp_csv="$tmp_dir/${zip_name%.zip}.csv"
  rm -f "$tmp_csv"
  ogr2ogr -f CSV "$tmp_csv" "$src" "portalpk_publi" \
    -lco GEOMETRY=AS_XY

  if (( first == 1 )); then
    cat "$tmp_csv" > "$output_csv"
    first=0
  else
    tail -n +2 "$tmp_csv" >> "$output_csv"
  fi
done

rm -f "$output_zip"
zip -j "$output_zip" "$output_csv" >/dev/null
echo "Done. Output: $output_zip"
