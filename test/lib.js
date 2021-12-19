const fs = require('fs');
const path = require('path');
const $RefParser = require('json-schema-ref-parser');

const GEOJSON = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/util/geojson.json')));

class OASchema {
    static async compile() {
        const v2 = await $RefParser.dereference(path.resolve(path.resolve(__dirname, '../schema/'), 'source_schema_v2.json'));

        return {
            geojson: GEOJSON,
            schema: {
                2: v2
            }
        }
    }
}

module.exports = OASchema;
