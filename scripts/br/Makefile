fetch:
	mkdir -p downloads
	wget -N -nv -P downloads/ -r ftp://ftp.ibge.gov.br/Censos/Censo_Demografico_2010/Cadastro_Nacional_de_Enderecos_Fins_Estatisticos/
        wget -N -nv -P downloads/ -r ftp://geoftp.ibge.gov.br/recortes_para_fins_estatisticos/malha_de_setores_censitarios/censo_2010/base_de_faces_de_logradouros/

unpack:
	mkdir -p data
	find downloads/ -name "*.zip" -exec unzip -d data/ {} \;
	find downloads -name "composição*.xls" -exec in2csv {} > data/manifest.csv \;

by_state:
	mkdir by_state
	for a in 11 12 13 14 15 16 17 21 22 23 24 25 26 27 28 29 31 32 33 35 41 42 43 50 51 52 53; do \
	    python3 parse_cnefe.py $$a > $$a.csv ;\
	    zip by_state/br-$$a.zip $$a.csv ;\
	done
