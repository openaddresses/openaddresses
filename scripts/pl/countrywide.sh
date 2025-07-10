#!/usr/bin/env bash

# CONFIG
ZIPFILE="PRG-punkty_adresowe.zip"
WORKDIR="unzipped"
OUTDIR="csv_output"

# Uncomment this line to download the ZIP automatically
wget -O "$ZIPFILE" "https://opendata.geoportal.gov.pl/prg/adresy/PRG-punkty_adresowe.zip"

# Create directories
mkdir -p "$WORKDIR"
mkdir -p "$OUTDIR"

# Uncomment this line if you want to unzip
unzip -o "$ZIPFILE" -d "$WORKDIR"

# Loop over extracted files
for FILE in "$WORKDIR"/*.xml; do
    [[ -e "$FILE" ]] || continue

    BASENAME=$(basename "$FILE")
    # Extract part after last double underscore "__"
    CLEAN_NAME=$(echo "$BASENAME" | sed -E 's/^.*__//; s/^([0-9]+_)+//; s/\.xml$//')
    CSVNAME="${CLEAN_NAME}.csv"
    CSVPATH="$OUTDIR/$CSVNAME"
    ZIPPATH="$OUTDIR/${CSVNAME}.zip"

    echo "Converting layer PRG_PunktAdresowy in $FILE to $CSVPATH with split list fields"

    # Convert with splitlistfields
    ogr2ogr \
        -f CSV "$CSVPATH" "$FILE" \
        "PRG_PunktAdresowy" \
        -lco GEOMETRY=AS_XY \
        -splitlistfields

    # Zip the CSV
    echo "Zipping $CSVNAME"
    zip -j "$ZIPPATH" "$CSVPATH"
done

echo "Conversion and zipping complete."