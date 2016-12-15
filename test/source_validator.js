var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request'),
    validator = require('validator'),
    versionCurrent = require('../package.json').version.split('.'),
    Ajv = require('ajv'),
    schema = require('../schema/source_schema.json');

var ajv = new Ajv( { extendRefs: true} );
var validate = ajv.compile(schema);

var manifest = glob.sync('sources/**/*.json');
var index = 0;

//Ensure tests on branch are current with master
request.get('https://raw.githubusercontent.com/openaddresses/openaddresses/master/package.json', function(err, res, masterPackage) {
    var versionMaster = JSON.parse(masterPackage).version.split('.');

    for (var i = 0; i < 3; i++) {
        if (versionMaster[i] > versionCurrent[i]) {
            console.log("Branch outdated! - Please pull new changes from openaddresses/openaddresses:master");
            process.exit(1);
        }
    }
    checkSource(index);
});

function validateJSON(body) {
    try {
        var data = JSON.parse(body);
        return data;
    } catch(e) {
        return null;
    }
}

function checkSource(i){
    var source = manifest[i];

    if (i === manifest.length || !source) {process.exit(0);}

    test(source, function(t) {
        var raw = fs.readFileSync(source, 'utf8');

        var data = validateJSON(raw);

        var valid = validate(data);
        if (!valid) {
          console.error(JSON.stringify(validate.errors, null, 2));
        }

        t.ok(valid, validate.errors);
        t.end();
        checkSource(++index);
    });
}
