TMP = /tmp/openaddresses-si/
TS = $$(cat $(TMP)timestamp.txt)
TSYYYY = $$(cat $(TMP)timestamp.txt | cut -b 1-4)

all:
	mkdir -p $(TMP) || true
	./getSource.sh $(TMP)

	# poor-man's git submodule:
	if [ ! -d "./GeoCoordinateConverter" ];then \
		git clone https://github.com/mrihtar/GeoCoordinateConverter ; \
	fi

	cd GeoCoordinateConverter && $(MAKE) -f Makefile.unix gk-shp

	rm -r $(TMP)HS-etrs89 || true
	mkdir -p $(TMP)HS-etrs89
	./GeoCoordinateConverter/gk-shp -t 9 -dd $(TMP)HS/SI.GURS.RPE.PUB.HS.shp $(TMP)HS-etrs89/SI.GURS.RPE.PUB.HS-etrs89.shp

	./makeCSVs.sh $(TMP)
	python addNames.py $(TMP)
	wc -l $(TMP)si-addresses-$(TS).csv
	head -n15 $(TMP)si-addresses-$(TS).csv

	# publish zips:
	sed "s/%YYYY-MM-DD%/$(TS)/g" LICENSE-data-template.txt > $(TMP)LICENSE-data.txt
	zip -9 -j $(TMP)si-addresses-$(TS).zip $(TMP)si-addresses-$(TS).csv $(TMP)LICENSE-data.txt
	cp $(TMP)si-addresses-$(TS).zip .
	cp $(TMP)si-addresses-$(TS).zip /osm/wwwroot/osm.si/openaddresses/
	cp $(TMP)si-addresses-$(TS).zip /osm/wwwroot/osm.si/openaddresses/si-addresses-latest.zip
	#bash -c "aws s3 cp $(TMP)si-addresses-$(TS).zip s3://data.openaddresses.io/cache/si-addresses-$(TS).zip"

	# update json:
	sed "s/%YYYY-MM-DD%/$(TS)/g" countrywide-template.json | sed "s/%YYYY%/$(TSYYYY)/g" > ../../sources/si/countrywide.json 

clean:
	rm -r $(TMP)
	if [ -d "./GeoCoordinateConverter" ];then \
		cd GeoCoordinateConverter && $(MAKE) -f Makefile.unix clean ; \
	fi

