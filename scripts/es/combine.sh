# write header
ls build | grep "A.ES" | head -n 1 | xargs -I {} head -n 1 build/{} > tee es.csv

# combine CSVs, stripping headers
for a in $(find build | grep csv) 
do 
    tail -n +2 $a >> es.csv
done