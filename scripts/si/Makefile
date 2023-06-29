TMP = /tmp/openaddresses-si/
PUBDIR = /osm/raba/raba.openstreetmap.si/openaddresses/

TSBLDG=$$(stat -c '%y' $(TMP)KS_SLO_SHP_G/KS_SLO_TLORISI_*.shp  | cut -d' ' -f1)
TSYYYY = $$(echo $(TSBLDG) | cut -b 1-4)

all: buildings

download:
	mkdir -p $(TMP) || true
	./getSource.sh $(TMP)

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
	sed "s/%YYYY-MM-DD%/$(TSBLDG)/g" countrywide-template.json | sed "s/%YYYY%/$(TSYYYY)/g" > ../../sources/si/countrywide.json

clean:
	rm -rf $(TMP)
