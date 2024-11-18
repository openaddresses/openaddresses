# write header
rm -f es.csv
touch es.csv
ls build | grep "es-" | head -n 1 | xargs -I {} head -n 1 build/{} > es.csv

# combine CSVs, stripping headers
for a in $(find build | grep csv)
do
    tail -n +2 $a >> es.csv
done
