var tape = require('tape'),
    glob = require('glob'),
    fs = require('fs'),
    Ajv = require('ajv'),
    request = require('request'),
    schema = require('../schema/source_schema.json');

var ajv = new Ajv( { loadSchema: loadSchema } );

// the schema contains a remote schema for geojson so it must be loaded async
ajv.compileAsync(schema, (err, validate) => {
  if (err) return;
  testAllSources(validate);
});

// this function instructs Ajv on how to load remote sources
function loadSchema(uri, callback) {
  request.get({url:uri}, (err, res, body) => {
    if (err || res.statusCode >= 400) {
      callback(err || new Error('Loading error: ' + res.statusCode));
    } else {
      callback(null, JSON.parse(body));
    }
  });
}

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
