.PRECIOUS: xml spain_catastre/gml build

all: es.csv

xml:
	curl -L "https://www.catastro.minhap.es/INSPIRE/Addresses/ES.SDGC.AD.atom.xml" | grep enclosure | sed -e "s/^.*http/http/" -e "s/\" type.*$$//" > xml_urls.txt
	mkdir xml
	cd xml && cat ../xml_urls.txt | xargs -I {} curl -L {} -O

spain_catastre/gml: xml
	rm -rf spain_catastre
	mkdir spain_catastre
	rm -f gml_urls.txt
	grep -a zip xml/* | sed -e "s/^.*http/http/" -e "s/\" type=.*$$//" | grep -a -v "</id" | grep -a -v "<inspire" >> spain_catastre/gml_urls.latin1.txt
	cat spain_catastre/gml_urls.latin1.txt | iconv -f latin1 -t utf8 > spain_catastre/gml_urls.txt
	rm -f spain_catastre/gm_urls.latin1.txt
	mkdir spain_catastre/gml
	python download_gml.py spain_catastre/gml_urls.txt spain_catastre/gml/

build: spain_catastre/gml
	mkdir -p build
	rm -f build/es-*.csv
	find spain_catastre/gml/ | grep zip | grep gml | parallel --no-notice -t -j 1 python gml_to_csv.py {} build/

es.csv: build
	bash ./combine.sh

# NOTE: you may also need to run find_missing.py to locate files that don't convert properly
