import requests

url = "https://xgis.maaamet.ee/adsavalik/valjav6te/"

r = requests.get(url)

for x in r.json():
  if x["vvnr"] == 1:
    if "kov" not in x:
      file = x["fail"]

data_url = url + file

#use data_url to import latest zip
