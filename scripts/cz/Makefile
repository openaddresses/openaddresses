# download:
# 	mkdir data
# 	cd data && cat seznamlinku.txt | parallel -j 3 curl '{}' -O

process:
	rm -f cz-*.csv
	find ./data -type f -name '*.gz' | parallel -j1 ./process_one.sh {}
