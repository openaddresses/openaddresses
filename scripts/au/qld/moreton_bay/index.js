#!/usr/bin/env node

const geojsonStream = require('geojson-stream');
const fs = require('fs');
const out = fs.createWriteStream('moreton_bay.openaddresses.geojson');
fs
  .createReadStream(`moreton_bay.geojson`)
  .pipe(geojsonStream.parse((feature, index) => {
    if (process.stdout.isTTY && index % 1000 === 0) {
      process.stdout.write(` ${index.toLocaleString()}\r`)
    }

    if (feature.properties.ADDRESS) {
      const start = feature.properties.ADDRESS.startsWith(feature.properties.HOUSE_NO) ? feature.properties.HOUSE_NO.length : 0
      const end = feature.properties.ADDRESS.endsWith(feature.properties.LOCALITY) ? feature.properties.ADDRESS.length - feature.properties.LOCALITY.length : undefined
      feature.properties.STREET = feature.properties.ADDRESS.slice(start, end).trim()
    }
    return feature
  }))
  .pipe(geojsonStream.stringify())
  .pipe(out);
