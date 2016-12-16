var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request'),
    versionCurrent = require('../package.json').version.split('.'),
    Ajv = require('ajv'),
    schema = require('../schema/source_schema.json');

var ajv = new Ajv( { loadSchema: loadSchema } );

// the schema contains a remote schema for geojson so it must be loaded async
ajv.compileAsync(schema, function (err, validate) {
  if (err) return;
  testAllSources(validate);
});

// this function instructs Ajv on how to load remote sources
function loadSchema(uri, callback) {
  request.get({url:uri}, function(err, res, body) {
    if (err || res.statusCode >= 400) {
      callback(err || new Error('Loading error: ' + res.statusCode));
    } else {
      callback(null, JSON.parse(body));
    }
  });
}

function testAllSources(validate) {
  //Ensure tests on branch are current with master
  request.get('https://raw.githubusercontent.com/openaddresses/openaddresses/master/package.json', function(err, res, masterPackage) {
    var versionMaster = JSON.parse(masterPackage).version.split('.');

    for (var i = 0; i < 3; i++) {
      if (versionMaster[i] > versionCurrent[i]) {
        console.log("Branch outdated! - Please pull new changes from openaddresses/openaddresses:master");
        process.exit(1);
      }
    }

    test('schema-validate sources', function(t) {
      // find all the sources
      var manifest = glob.sync('sources/**/*.json');

      manifest.forEach(function(source) {
        var data = JSON.parse(fs.readFileSync(source, 'utf8'));

        var valid = validate(data);

        t.notOk(validate.errors, source);

      });

      t.end();

    });

  });
}
