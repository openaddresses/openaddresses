var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request'),
    versionCurrent = require('../package.json').version.split('.'),
    Ajv = require('ajv'),
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
  //Ensure tests on branch are current with master
  request.get('https://raw.githubusercontent.com/openaddresses/openaddresses/master/package.json', (err, res, masterPackage) => {
    var versionMaster = JSON.parse(masterPackage).version.split('.');

    for (var i = 0; i < 3; i++) {
      if (versionMaster[i] > versionCurrent[i]) {
        console.log("Branch outdated! - Please pull new changes from openaddresses/openaddresses:master");
        process.exit(1);
      }
    }

    // find all the sources
    glob.sync('sources/**/*.json').forEach((source) => {
      test(`schema-validation for source ${source}`, (t) => {
        try {
          var data = JSON.parse(fs.readFileSync(source, 'utf8'));
          var valid = validate(data);

          t.notOk(validate.errors, source, 'schema validation failed');

        } catch (err) {
          t.fail(`could not parse ${source} as JSON: ${err}`);
        }

        t.end();

      });

    });

  });
}
