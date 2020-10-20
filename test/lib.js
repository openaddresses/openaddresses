const fs = require('fs');
const path = require('path');

const SCHEMA_V1 = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/source_schema.json')));
const SCHEMA_V2 = JSON.parse(fs.readFileSync(path.resolve(__dirname, '../schema/source_schema_v2.json')));

module.exports = {
    schema: {
        1: SCHEMA_V1,
        2: SCHEMA_V2
    }
}
