'use strict';

const request = require('request');
const fs = require('fs-extra');
const _ = require('lodash');
const path = require('path');

const output_filename = path.resolve('data', 'us-il-cook.geojson');

let count = 0;

const sections = [
  'qzpp-jhf6',
  '4977-ijic',
  '7832-c962',
  '5krr-vb4m',
  '38yg-b73x',
  'nkzg-ucit',
  'rxi4-nx3v',
  'ivv7-q3um',
  'syzq-55pd',
  'c4y3-uesx',
  'uf63-xagj',
  '6265-sdqf',
  '6y64-fiuv',
  '7rcp-cifk',
  'ai6s-9ihv',
  'e9gq-iquy',
  'jaeu-u2u6',
  'b83i-7zxa',
  'y9wi-jd57',
  '24hu-vx3h',
  'uhv8-ar4p',
  'mqn9-4wmy',
  'kkvn-vsd7',
  'ntax-x2zf',
  '6uxp-xqj6',
  'pz8d-arh6',
  'vhk7-x9yc',
  'gug2-e5qv',
  'd8c2-rize',
  'k7z8-ma9h',
  'mqsd-unjm',
  'q6ik-zx2p',
  '7fn9-axdp'
];

fs.ensureDirSync('data');

sections.forEach((section) => {
  const url = `https://datacatalog.cookcountyil.gov/api/geospatial/${section}?method=export&format=GeoJSON`;

  request(url).pipe(fs.createWriteStream(`data/${section}.geojson`)).on('finish', () => {
    console.log(`retrieved ${section} (${count+1}/${sections.length})`);

    if (++count === sections.length) {
      console.log(`finished retrieving ${sections.length} sections`);
      dumpToOneBigFile();
    }

  });

});

function dumpToOneBigFile() {
  const write_stream = fs.createWriteStream(output_filename);
  write_stream.write('{"type":"FeatureCollection","features":[\n');

  sections.forEach((section, section_idx) => {
    const contents = JSON.parse(fs.readFileSync(path.resolve('data', `${section}.geojson`)));

    console.log(`read ${contents.features.length} features from ${section} (${section_idx+1}/${sections.length})`);

    contents.features.forEach((feature, feature_idx) => {
      feature.properties = _.pick(feature.properties, ['addrnocom', 'stnamecom', 'placename', 'zip5']);
      write_stream.write(JSON.stringify(feature));

      if (section_idx < sections.length-1 || feature_idx < contents.features.length-1) {
        write_stream.write(',');
      }

      write_stream.write('\n');

    });

  });

  write_stream.write(']}');
  console.log(`finished writing ${sections.length} sections to ${output_filename}`);

}
