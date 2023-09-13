# download:
# 	mkdir data
# 	cd data && cat seznamlinku.txt | parallel -j 3 curl '{}' -O

process:
	rm -f cz-*.csv cz.log
	find /mnt/data/cz -type f -name '*.gz' | parallel -j4 ./process_one.sh {}
	mkdir processed || true
	mv *.csv processed/

combine:
	bash -c "for a in processed/*.csv; do ROOT=\"\$$(basename \$$a | sed 's/_.*//')_combined\"; if [ ! -f \$$ROOT ]; then head -n1 \$$(find processed -type f -name \"*.csv\" | head -n 1) > \$$ROOT; fi; cat \$$a | tail -n+2 >> \$$ROOT; echo \$$a; done"
	bash -c "for a in *_combined; do mv \$$a \$$(basename \$$a _combined).csv; done"
	bash -c "zip cz-\$$(date '+%Y%m%d').zip *.csv"

upload:
	aws s3 cp cz-*.zip s3://data.openaddresses.io/cache/
