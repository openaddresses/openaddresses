var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request');
    versionCurrent = require('../package.json').version.split('.');

    var manifest = glob.sync('sources/*.json');
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

    if (i == manifest.lenght-1 || !source) process.exit(0);

    test(source, function(t) {
        var raw = fs.readFileSync(source, 'utf8');
        var data = validateJSON(raw);

        t.ok(data, "Data is valid JSON");

        if (data) {
            if (data.skip) t.pass("WARN - Skip Flag Detected");

            //Ensure people don't make up values
            generalOptions = ['email', 'attribution', 'year', 'skip', 'conform', 'coverage', 'data', 'compression', 'type', 'coverage', 'website', 'license', 'note'];

            Object.keys(data).forEach(function (generalKey) {
                t.ok(generalOptions.indexOf(generalKey) !== -1, generalKey + " is supported");
            });

            //Mandatory Fields & Coverage
            t.ok(data.data, "Checking for data");
            t.ok(data.type, "Checking for type");
            if (data.compression && ['zip'].indexOf(data.compression) === -1) t.fail("Compression type not supported");
            t.ok(typeof data.coverage === 'object', "Coverage Object Exists");
            t.ok(typeof data.coverage.country === 'string', "coverage - Country must be a string");
            t.ok(data.coverage.province ? typeof data.coverage.country === 'string' : true, "coverage - Province must be a string");
            t.ok(data.coverage.county ? typeof data.coverage.county === 'string' : true, "coverage - County must be a string");
            t.ok(data.coverage.city ? typeof data.coverage.city === 'string' : true, "coverage - City must be a string");
            t.ok(['http', 'ftp', 'ESRI'].indexOf(data.type) !== -1, "Type valid");

            if (data.conform) {
                //Ensure people don't make up new values
                var conformOptions = ['type', 'csvsplit', 'merge', 'advanced_merge', 'split', 'srs', 'file', 'encoding', 'headers', 'skiplines', 'lon', 'lat', 'number', 'street', 'city', 'postcode', 'district', 'region', 'addrtype', 'notes', 'accuracy'];
                Object.keys(data.conform).forEach(function (conformKey) {
                    t.ok(conformOptions.indexOf(conformKey) !== -1, "conform - " + conformKey + " is supported");
                });

                //Mandatory Conform Fields
                t.ok(data.conform.number && typeof data.conform.number === 'string', "conform - number attribute required");
                t.ok(data.conform.street && typeof data.conform.street === 'string', "conform - street attribute required");
                t.ok(data.conform.type && typeof data.conform.type === 'string', "conform - type attribute required");
                t.ok(['shapefile', 'shapefile-polygon', 'csv', 'geojson', 'xml'].indexOf(data.conform.type) !== -1, "conform - type is supported");
                if (data.conform.type === 'csv') {
                    t.ok(data.conform.lon && typeof data.conform.lon === 'string', "conform - lon attribute required for type csv");
                    t.ok(data.conform.lat && typeof data.conform.lat === 'string', "conform - lat attribute required for type csv");
                }

                //Optional Conform Fields
                t.ok(data.conform.merge ? Array.isArray(data.conform.merge) : true, "conform - Merge is an array");
                t.ok(data.conform.addrtype ? typeof data.conform.addrtype === 'string' : true, "conform - addrtype is a string");
                t.ok(data.conform.accuracy ? typeof data.conform.accuracy === 'number' : true, "conform - accuracy is a number");
                t.ok(data.conform.accuracy ? data.conform.accuracy !== 0 : true, "conform - accuracy is not 0");
                t.ok(data.conform.csvsplit ? typeof data.conform.csvsplit === 'string' : true, "conform - csvsplit is a string");
                t.ok(data.conform.split ? typeof data.conform.split === 'string' : true, "conform - split is a string");
                t.ok(data.conform.srs ? typeof data.conform.srs === 'string' : true, "conform - srs is a string");
                t.ok(data.conform.file ? typeof data.conform.file === 'string' : true, "conform - file is a string");
                t.ok(data.conform.encoding ? typeof data.conform.encoding === 'string' : true, "conform - encoding is a string");
                t.ok(data.conform.city ? typeof data.conform.city === 'string' : true, "conform - city is a string");
                t.ok(data.conform.postcode ? typeof data.conform.postcode === 'string' : true, "conform - postcode is a string");
                t.ok(data.conform.district ? typeof data.conform.district === 'string' : true, "conform - district is a string");
                t.ok(data.conform.region ? typeof data.conform.region === 'string' : true, "conform - region is a string");
                t.ok(data.conform.addrtype ? typeof data.conform.addrtype === 'string' : true, "conform - addrtype is a string");
                t.ok(data.conform.notes ? typeof data.conform.notes === 'string' : true, "conform - notes is a string");
            }

            //Optional General Fields
            t.ok(data.coverage.email ? typeof data.coverage.email === 'string' : true, "email must be a string");
            t.ok(data.coverage.website ? typeof data.coverage.website === 'string' : true, "website must be a string");
            t.ok(data.coverage.license ? typeof data.coverage.license === 'string' : true, "license must be a string");
        }
        t.end();
        checkSource(++index);
    });
}
