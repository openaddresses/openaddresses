const tape = require('tape');
const glob = require('glob');
const fs = require('fs');
const Ajv = require('ajv');
const request = require('request');
const schema_v2 = require('../schema/source_schema_v2.json');
const addFormats = require("ajv-formats")

const ajv = new Ajv();
addFormats(ajv)
ajv.addMetaSchema(require('../schema/geojson.json'));

const validate_v2 = ajv.compile(schema_v2);

// find all the sources, has to be synchronous for tape
glob.sync('sources/**/*.json').forEach((source) => {
    tape(`tests for ${source}`, (t) => {
        try {
            const data = JSON.parse(fs.readFileSync(source, 'utf8'));

            let valid = true;
            valid = validate_v2(data);
            t.ok(valid, `${source}: ${JSON.stringify(validate_v2.errors)}`);
        } catch (err) {
            t.fail(`could not parse ${source} as JSON: ${err}`);
        }

        t.end();
    });
});
