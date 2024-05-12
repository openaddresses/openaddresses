all: build

download:
	curl -s -O https://www150.statcan.gc.ca/n1/pub/46-26-0002/2022001/2023.zip

build: download
	python3 process.py
	gzip canada-nar-combined.csv
