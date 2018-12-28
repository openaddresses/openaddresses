all:
	mkdir -p /tmp/at || true
	bash -c "if [ ! -f /tmp/at/at-in.zip ]; then curl 'http://www.bev.gv.at/pls/portal/docs/PAGE/BEV_PORTAL_CONTENT_ALLGEMEIN/0200_PRODUKTE/UNENTGELTLICHE_PRODUKTE_DES_BEV/Adresse_Relationale_Tabellen-Stichtagsdaten.zip' > /tmp/at/at-in.zip; unzip -d /tmp/at/ /tmp/at/at-in.zip; fi"
	python split.py /tmp/at/ADRESSE.CSV /tmp/at/STRASSE.csv > timestamp.txt
	cp at-*.json ../../sources/at/
	zip /tmp/at/at-out.zip at-*.csv
	bash -c "aws s3 cp /tmp/at/at-out.zip s3://data.openaddresses.io/cache/at-$$(cat timestamp.txt).zip"
	rm -f timestamp.txt
