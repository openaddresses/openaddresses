const fs = require('fs');
const path = require('path');
const $RefParser = require('json-schema-ref-parser');

const Ajv = require('ajv');
const addFormats = require("ajv-formats")

const GEOJSON = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/util/geojson.json')));
const base = {
    geojson: GEOJSON,
    schema: { }
};

/**
 * @class
 *
 * @param {Boolean} [ajv=false] Optionally return AJV instance instead of compiled schema
 */
class OASchema {
    static async compile(ajv) {
        base.schema['2'] = await $RefParser.dereference(path.resolve(path.resolve(__dirname, '../schema/'), 'source_schema_v2.json'));
        if (!ajv) return base;

        const ajvi = new Ajv({
            allErrors: true
        });

        addFormats(ajvi)
        return ajvi.compile(base.schema['2']);
    }
}

module.exports = OASchema;
