#!/bin/bash
set -euxo pipefail

curl -OL https://www.avoindata.fi/data/dataset/cf9208dc-63a9-44a2-9312-bbd2c3952596/resource/ae13f168-e835-4412-8661-355ea6c4c468/download/suomi_osoitteet_2024-05-14.7z
7z x suomi_osoitteet_2024-05-14.7z
zip suomi_osoitteet_2024-05-14.zip Suomi_osoitteet_2024-05-14.OPT
