const fs = require('fs');
const path = require('path');

const GEOJSON = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/geojson.json')));
const SCHEMA_V2 = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/source_schema_v2.json')));

// Only returns actively supported versions
module.exports = {
    geojson: GEOJSON,
    schema: {
        2: SCHEMA_V2
    }
}
