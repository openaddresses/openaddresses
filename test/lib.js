const fs = require('fs');
const path = require('path');
const $RefParser = require('json-schema-ref-parser');

const GEOJSON = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/util/geojson.json')));
const SCHEMA_V2 = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/source_schema_v2.json')));

class OASchema {
    static async compile() {
        await $RefParser.dereference(path.resolve(path.resolve(__dirname, '../schema/'), 'source_schema_v2.json'));
    }
}

module.exports = {
    geojson: GEOJSON,
    schema: {
        2: SCHEMA_V2
    }
}
