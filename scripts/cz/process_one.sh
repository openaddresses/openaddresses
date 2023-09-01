DIR="$(dirname $1)"
XML="$(basename $1 .gz)"
gunzip "$1"
python process_cz_gml.py "$DIR/$XML" 2>/dev/null | tee -a cz.log
gzip -9 "$DIR/$XML"
