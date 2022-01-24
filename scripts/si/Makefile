TMP = /tmp/openaddresses-si/
PUBDIR = /osm/raba/raba.openstreetmap.si/openaddresses/
TS = $$(cat $(TMP)timestamp.txt)
TSYYYY = $$(cat $(TMP)timestamp.txt | cut -b 1-4)

TSBLDG=$$(stat -c '%y' $(TMP)KS_SLO_SHP_G/KS_SLO_TLORISI_*.shp  | cut -d' ' -f1)

all: addresses buildings

download:
	mkdir -p $(TMP) || true
	./getSource.sh $(TMP)

addresses: download
	./makeCSVs.sh $(TMP)
	python addNames.py $(TMP)
	wc -l $(TMP)si-addresses-$(TS).csv
	head -n15 $(TMP)si-addresses-$(TS).csv

	# publish zips:
	sed "s/%YYYY-MM-DD%/$(TS)/g" LICENSE-data-template.txt > $(TMP)LICENSE-data.txt
	zip -9 -j $(TMP)si-addresses-$(TS).zip $(TMP)si-addresses-$(TS).csv $(TMP)LICENSE-data.txt
	#cp $(TMP)si-addresses-$(TS).zip .
	mv $(TMP)si-addresses-$(TS).zip $(PUBDIR)
	ln -sf si-addresses-$(TS).zip $(PUBDIR)si-addresses-latest.zip
	cp $(TMP)si-addresses-$(TS).csv $(PUBDIR)si-addresses-latest.csv
	#bash -c "aws s3 cp $(TMP)si-addresses-$(TS).zip s3://data.openaddresses.io/cache/si-addresses-$(TS).zip"

buildings: download
	rm -rf $(TMP)KS_SLO_SHP_G_TLORISI
	ogr2ogr -s_srs "EPSG:3794" -t_srs "EPSG:4326" \
		$(TMP)KS_SLO_SHP_G_TLORISI \
		$(TMP)KS_SLO_SHP_G/KS_SLO_TLORISI_????????.shp \
		-nln KS_SLO_SHP_G_TLORISI -progress

	sed "s/%YYYY-MM-DD%/$(TSBLDG)/g" LICENSE-buildings-template.txt > $(TMP)LICENSE-buildings.txt
	zip -9 -j $(TMP)si-buildings-$(TSBLDG).zip $(TMP)KS_SLO_SHP_G_TLORISI/* $(TMP)LICENSE-buildings.txt
	mv $(TMP)si-buildings-$(TSBLDG).zip $(PUBDIR)
	ln -sf si-buildings-$(TSBLDG).zip $(PUBDIR)si-buildings-latest.zip

	# update json:
	sed "s/%YYYY-MM-DD%/$(TS)/g" countrywide-template.json | sed "s/%YYYY%/$(TSYYYY)/g" > ../../sources/si/countrywide.json

clean:
	rm -rf $(TMP)
