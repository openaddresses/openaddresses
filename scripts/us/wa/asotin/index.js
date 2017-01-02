'use strict';

const fs = require('fs');
const arcgisToGeoJSON = require('arcgis-to-geojson-utils').arcgisToGeoJSON;

// the source is too big to load at once so stream it
const oboe = require('oboe');

const o = {
  type: 'FeatureCollection',
  features: []
};

// pull apart city/state/zip to make conform easier in source
const lastLineRegex = /^([A-Z]+) ([A-Z]+) ([0-9]+)$/

oboe('http://www.arcgis.com/sharing/rest/content/items/aebf050394024cf3befac2806b775efe/data?f=json')
  .node('operationalLayers[*].featureCollection.layers[0].featureSet.features.*', (feature) => {
    // only bother if there is a physical address
    if (feature.attributes.PA2.trim().length > 0) {
      // first convert from ESRI json to geojson
      feature = arcgisToGeoJSON(feature);

      // delete properties, we'll add back
      var props = feature.properties;
      delete feature.properties;

      feature.properties = {
        address: props.PA2
      };

      // figure out what the city/state/zip values are based on a regex
      const lastLine = props.PA3.replace(/,/g, ' ').replace(/\s+/g, ' ');
      const m = lastLine.match(lastLineRegex);

      if (m) {
        feature.properties.city = m[1]
        feature.properties.state = m[2]
        feature.properties.postalcode = m[3]
      }

      o.features.push(feature);

    }

  })
  .done(() => {
      fs.writeFile('asotin.geojson', JSON.stringify(o, null, 2), (err) => {
        if (err) throw err;
        console.log(`wrote ${o.features.length} features`);
      });

  });
