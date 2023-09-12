import fs from 'fs';
import $RefParser from 'json-schema-ref-parser';
import Ajv from 'ajv';
import addFormats from 'ajv-formats';

const GEOJSON = JSON.parse(fs.readFileSync(new URL('../schema/util/geojson.json', import.meta.url)));

const base = {
    geojson: GEOJSON,
    schema: { }
};

/**
 * @class
 *
 * @param {Boolean} [ajv=false] Optionally return AJV instance instead of compiled schema
 */
export default class OASchema {
    static async compile(ajv) {
        base.schema['2'] = await $RefParser.dereference(String(new URL('../schema/source_schema_v2.json', import.meta.url)));
        if (!ajv) return base;

        const ajvi = new Ajv({
            allErrors: true
        });

        addFormats(ajvi);
        return ajvi.compile(base.schema['2']);
    }
}
