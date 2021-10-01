TMP = /tmp/openaddresses-si/
TS = $$(cat $(TMP)timestamp.txt)
TSYYYY = $$(cat $(TMP)timestamp.txt | cut -b 1-4)

TSBLDG=$$(stat -c '%y' $(TMP)KS_SLO_SHP_G/KS_SLO_TLORISI_*.shp  | cut -d' ' -f1)

all:
	mkdir -p $(TMP) || true
	./getSource.sh $(TMP)

	./makeCSVs.sh $(TMP)
	python addNames.py $(TMP)
	wc -l $(TMP)si-addresses-$(TS).csv
	head -n15 $(TMP)si-addresses-$(TS).csv

	# publish zips:
	sed "s/%YYYY-MM-DD%/$(TS)/g" LICENSE-data-template.txt > $(TMP)LICENSE-data.txt
	zip -9 -j $(TMP)si-addresses-$(TS).zip $(TMP)si-addresses-$(TS).csv $(TMP)LICENSE-data.txt
	#cp $(TMP)si-addresses-$(TS).zip .
	mv $(TMP)si-addresses-$(TS).zip /osm/raba/raba.openstreetmap.si/openaddresses/
	ln -sf si-addresses-$(TS).zip /osm/raba/raba.openstreetmap.si/openaddresses/si-addresses-latest.zip
	cp $(TMP)si-addresses-$(TS).csv /osm/raba/raba.openstreetmap.si/openaddresses/si-addresses-latest.csv
	#bash -c "aws s3 cp $(TMP)si-addresses-$(TS).zip s3://data.openaddresses.io/cache/si-addresses-$(TS).zip"

	# buildings
	sed "s/%YYYY-MM-DD%/$(TSBLDG)/g" LICENSE-buildings-template.txt > $(TMP)LICENSE-buildings.txt
	zip -9 -j $(TMP)si-buildings-$(TSBLDG).zip $(TMP)KS_SLO_SHP_G/KS_SLO_TLORISI_* $(TMP)LICENSE-buildings.txt
	mv $(TMP)si-buildings-$(TSBLDG).zip /osm/raba/raba.openstreetmap.si/openaddresses/
	ln -sf si-buildings-$(TSBLDG).zip /osm/raba/raba.openstreetmap.si/openaddresses/si-buildings-latest.zip

	# update json:
	sed "s/%YYYY-MM-DD%/$(TS)/g" countrywide-template.json | sed "s/%YYYY%/$(TSYYYY)/g" > ../../sources/si/countrywide.json 
