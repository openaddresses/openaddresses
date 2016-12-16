var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request'),
    versionCurrent = require('../package.json').version.split('.'),
    Ajv = require('ajv'),
    schema = require('../schema/source_schema.json');

// all the sources
var manifest = glob.sync('sources/**/*.json');
var index = 0;

var ajv = new Ajv( { loadSchema: loadSchema } );

ajv.compileAsync(schema, function (err, validate) {
    if (err) return;
    testAllTheThings(validate);
});

function loadSchema(uri, callback) {
    request.get({url:uri}, function(err, res, body) {
        if (err || res.statusCode >= 400) {
            callback(err || new Error('Loading error: ' + res.statusCode));
        } else {
            callback(null, JSON.parse(body));
        }
    });
}

function testAllTheThings(validate) {
  //Ensure tests on branch are current with master
  request.get('https://raw.githubusercontent.com/openaddresses/openaddresses/master/package.json', function(err, res, masterPackage) {
      var versionMaster = JSON.parse(masterPackage).version.split('.');

      for (var i = 0; i < 3; i++) {
          if (versionMaster[i] > versionCurrent[i]) {
              console.log("Branch outdated! - Please pull new changes from openaddresses/openaddresses:master");
              process.exit(1);
          }
      }
      checkSource(index, validate);
  });
}

function checkSource(i, validate){
    var source = manifest[i];

    if (i === manifest.length || !source) {process.exit(0);}

    test(source, function(t) {
        var raw = fs.readFileSync(source, 'utf8');

        var data = JSON.parse(raw);

        var valid = validate(data);
        if (!valid) {
          console.error(JSON.stringify(validate.errors, null, 2));
        }

        t.ok(valid, validate.errors);
        t.end();
        checkSource(++index, validate);
    });
}
