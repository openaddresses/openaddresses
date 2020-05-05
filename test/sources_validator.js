const tape = require('tape');
const glob = require('glob');
const fs = require('fs');
const Ajv = require('ajv');
const request = require('request');
const schema = require('../schema/source_schema.json');

const ajv = new Ajv();
ajv.addMetaSchema(require('ajv/lib/refs/json-schema-draft-04.json'), "http://json-schema.org/draft-04/schema#");
ajv.addMetaSchema(require('./geojson.json'), "http://json.schemastore.org/geojson#/definitions/geometry");
testAllSources(ajv.compile(schema));

function testAllSources(validate) {
    // find all the sources, has to be synchronous for tape
    glob.sync('sources/**/*.json').forEach((source) => {
        tape(`tests for ${source}`, (test) => {
            test.test(`schema-validation for source ${source}`, (t) => {
                try {
                    const data = JSON.parse(fs.readFileSync(source, 'utf8'));
                    const valid = validate(data);

                    t.ok(valid, `${source}: ${JSON.stringify(validate.errors)}`);

                } catch (err) {
                    t.fail(`could not parse ${source} as JSON: ${err}`);
                }

                t.end();

            });

        });

    });

}
