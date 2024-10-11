import csv
import time
import zipfile
from pathlib import Path

import requests
from requests.adapters import HTTPAdapter
from urllib3 import Retry

start = time.time()

CNEFE_BASE_URL = (
    "https://ftp.ibge.gov.br/Cadastro_Nacional_de_Enderecos_para_Fins_Estatisticos/"
    "Censo_Demografico_2022/Arquivos_CNEFE/CSV/UF/"
)

# Define the order of tables for importing data
STATES_BY_CODE = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF",
}

STATE_FILES = [
    f"{state_code}_{STATES_BY_CODE[state_code]}.zip"
    for state_code in STATES_BY_CODE.keys()
]

download_path = Path("/tmp/cnefe")
download_path.mkdir(parents=True, exist_ok=True)

# Download all files
print("Downloading CNEFE 2022 CSV files from IBGE")
print("==========================================")
retry_strategy = Retry(
    total=3,
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
for state_file in STATE_FILES:
    print(f"Downloading {state_file}...", end="", flush=True)
    # Check if the file already exists before downloading
    if (download_path / state_file).exists():
        print(" File already exists. Skipping...")
        continue

    response = session.get(CNEFE_BASE_URL + state_file, timeout=10)
    if response.status_code != 200:
        print("Failed!")
        print(f"Status code: {response.status_code}")
        print(f"Reason: {response.reason}")
        exit(1)
    with Path.open(download_path / state_file, "wb") as f:
        f.write(response.content)
    print(f" Done! {len(response.content) / (1024 * 1024):.2f} MB downloaded.")

# Unzip all files
print()
print("Extracting all files")
print("====================")
for state_file in STATE_FILES:
    state_file_csv = state_file.replace(".zip", ".csv")
    print(f"Extracting {state_file}...", end="", flush=True)

    # Check if the file already exists before extracting
    if (download_path / state_file_csv).exists():
        print(f"File {state_file_csv} already extracted. Skipping...")
        continue

    with zipfile.ZipFile(download_path / state_file, "r") as zip_ref:
        zip_ref.extractall(download_path)
    print(" Done!")

# Create lookup tables for states, municipalities, districts, subdistricts
districts_by_code = {}
with open("data/RELATORIO_DTB_BRASIL_DISTRITO.csv", "r") as input_file:
    reader = csv.reader(input_file)
    header = next(reader)
    cod_distrito = header.index("Código de Distrito Completo")
    nome_distrito = header.index("Nome_Distrito")
    for row in reader:
        districts_by_code[row[cod_distrito].strip()] = row[nome_distrito].strip()

subdistricts_by_code = {}
with open("data/RELATORIO_DTB_BRASIL_SUBDISTRITO.csv", "r") as input_file:
    reader = csv.reader(input_file)
    header = next(reader)
    cod_subdistrito = header.index("Código de Subdistrito Completo")
    nome_subdistrito = header.index("Nome_Subdistrito")
    for row in reader:
        subdistricts_by_code[row[cod_subdistrito].strip()] = row[
            nome_subdistrito
        ].strip()

municipalities_by_code = {}
with open("data/RELATORIO_DTB_BRASIL_MUNICIPIO.csv", "r") as input_file:
    reader = csv.reader(input_file)
    header = next(reader)
    cod_municipio = header.index("Código Município Completo")
    nome_municipio = header.index("Nome_Município")
    for row in reader:
        municipalities_by_code[row[cod_municipio].strip()] = row[nome_municipio].strip()


# Get all CSV files in the base folder
csv_files = list(download_path.glob("*.csv"))

# Make sure the output folder exists
output_folder = Path("output")
output_folder.mkdir(parents=True, exist_ok=True)


def process_row(row: dict, output_header: list) -> list:
    # Build the address number
    number = row["NUM_ENDERECO"].strip()
    if row["DSC_MODIFICADOR"] == "KM":
        number = f"KM {number}"
    elif row["DSC_MODIFICADOR"] == "SN":
        number = "S/N"
    row["NUM_ENDERECO"] = number

    # Build the address street
    logradouro = row["NOM_TIPO_SEGLOGR"].strip()
    if row["NOM_TITULO_SEGLOGR"]:
        logradouro += " " + row["NOM_TITULO_SEGLOGR"].strip()
    logradouro += " " + row["NOM_SEGLOGR"].strip()
    row["LOGRADOURO"] = logradouro

    # Build the address complement
    complemento_parts = []
    if row["NOM_COMP_ELEM1"]:
        complemento_parts.append(row["NOM_COMP_ELEM1"])
    if row["VAL_COMP_ELEM1"]:
        complemento_parts.append(row["VAL_COMP_ELEM1"])
    if row["NOM_COMP_ELEM2"]:
        complemento_parts.append(row["NOM_COMP_ELEM2"])
    if row["VAL_COMP_ELEM2"]:
        complemento_parts.append(row["VAL_COMP_ELEM2"])
    if row["NOM_COMP_ELEM3"]:
        complemento_parts.append(row["NOM_COMP_ELEM3"])
    if row["VAL_COMP_ELEM3"]:
        complemento_parts.append(row["VAL_COMP_ELEM3"])
    if row["NOM_COMP_ELEM4"]:
        complemento_parts.append(row["NOM_COMP_ELEM4"])
    if row["VAL_COMP_ELEM4"]:
        complemento_parts.append(row["VAL_COMP_ELEM4"])
    if row["NOM_COMP_ELEM5"]:
        complemento_parts.append(row["NOM_COMP_ELEM5"])
    if row["VAL_COMP_ELEM5"]:
        complemento_parts.append(row["VAL_COMP_ELEM5"])
    row["COMPLEMENTO"] = " ".join(complemento_parts)

    # Build the address city
    row["MUNICIPIO"] = municipalities_by_code.get(row["COD_MUNICIPIO"], "")

    # Build the address district
    row["DISTRITO"] = districts_by_code.get(row["COD_DISTRITO"], "")

    # Build the address subdistrict
    row["SUBDISTRITO"] = subdistricts_by_code.get(row["COD_SUBDISTRITO"], "")

    # Build the address state
    row["UF"] = STATES_BY_CODE.get(row["COD_UF"], "")

    # Format the address data using the output header
    address_data = []
    for header in output_header:
        address_data.append(row.get(header, ""))
    return address_data


output_header = [
    "COD_UNICO_ENDERECO",
    "UF",
    "DISTRITO",
    "SUBDISTRITO",
    "MUNICIPIO",
    "COD_SETOR",
    "NUM_QUADRA",
    "NUM_FACE",
    "CEP",
    "DSC_LOCALIDADE",
    "LOGRADOURO",
    "NUM_ENDERECO",
    "COMPLEMENTO",
    "LATITUDE",
    "LONGITUDE",
    "NV_GEO_COORD",
    "COD_TIPO_ESPECI",
    "DSC_ESTABELECIMENTO",
    "COD_ESPECIE",
]

# Process each CSV file
print()
print("Processing all files")
print("====================")
for csv_file in csv_files:
    output_file = output_folder / csv_file.name
    print(f"Generating {output_file}...", end="", flush=True)
    with open(csv_file, "r") as input_file, open(output_file, "w") as output_file:
        uf_code = csv_file.name.split("_")[0]
        geojson_name = f"qg_810_endereco_UF{uf_code}"

        # Write the header
        output_file.write(",".join(output_header) + "\n")

        reader = csv.DictReader(input_file, delimiter=";")

        # Read each row
        for row in reader:
            # Skip rows with no latitude or longitude
            if not row["LATITUDE"] or not row["LONGITUDE"]:
                continue

            # Process the row
            address_data = process_row(row, output_header)

            # Write the row to the output file
            output_file.write(",".join(address_data) + "\n")
        print(" Done!")

print("==========================================")
print("Finished processing all files.")
duration = time.time() - start
print(f"Total time: {duration:.2f} seconds")
