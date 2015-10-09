var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request');
    versionCurrent = require('../package.json').version.split('.');

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

    if (i == manifest.lenght-1 || !source) process.exit(0);

    test(source, function(t) {
        var raw = fs.readFileSync(source, 'utf8');
        var data = validateJSON(raw);

        t.ok(data, "Data is valid JSON");

        if (data) {
            if (data.skip) t.pass("WARN - Skip Flag Detected");

            // Ensure people don't make up tags
            legalTags = [
                // https://github.com/openaddresses/openaddresses/blob/master/CONTRIBUTING.md#core-tags
                'data', 'type', 'coverage', 'coverage', 'conform', 'compression',
                
                // https://github.com/openaddresses/openaddresses/blob/master/CONTRIBUTING.md#optional-tags
                'website', 'license', 'note', 'attribution', 'email',
                
                // Not documented, but works
                'year', 'skip'
                ]

            Object.keys(data).forEach(function (userTag) {
                t.ok(legalTags.indexOf(userTag) !== -1, '"'+userTag+'" is not a tag documented in CONTRIBUTING.md.');
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
            t.ok(['http', 'ftp', 'esri'].indexOf(data.type.toLowerCase()) !== -1, "Type valid");

            if (data.conform) {
                //Ensure people don't make up new values
                var conformOptions = [
                    'type', 'csvsplit', 'split', 'srs',
                    'file', 'encoding', 'headers', 'skiplines', 'lon', 'lat',
                    'number', 'street', 'city', 'postcode', 'district',
                    'region', 'addrtype', 'notes', 'accuracy', 'id'
                    ];
                Object.keys(data.conform).forEach(function (conformKey) {
                    t.ok(conformOptions.indexOf(conformKey) !== -1, 'conform - "' + conformKey + '" is not a recognized attribute tag');
                });

                //Mandatory Conform Fields
                t.ok(data.conform.type && typeof data.conform.type === 'string', "conform - type attribute required");
                t.ok(['shapefile', 'shapefile-polygon', 'csv', 'geojson', 'xml'].indexOf(data.conform.type) !== -1, "conform - type is supported");
                if (data.conform.type === 'csv') {
                    t.ok(data.conform.lon && typeof data.conform.lon === 'string', "conform - lon attribute required for type csv");
                    t.ok(data.conform.lat && typeof data.conform.lat === 'string', "conform - lat attribute required for type csv");
                } else {
                    t.ok(!data.conform.lon, 'lon should only be set for csv type');
                    t.ok(!data.conform.lat, 'lat should only be set for csv type');
                }
                t.ok(data.conform.number, "conform - number attribute required");
                t.ok(data.conform.street, "conform - street attribute required");

                //Conform Attributes
                ['number', 'street', 'city', 'postcode', 'district', 'region', 'notes'].forEach(function(attrib) {
                    if (!data.conform[attrib]) { return; }
                    if (typeof data.conform[attrib] === 'string') {
                        t.ok(data.conform[attrib], attrib + ' references static field');
                    } else if (Array.isArray(data.conform[attrib])) {
                        t.ok(data.conform[attrib].length > 1, 'merge array has more than 1 element');
                        t.ok(data.conform[attrib], attrib + ' references fields to be merged');
                    } else if (typeof data.conform[attrib] === 'object') {
                        t.ok(data.conform[attrib].function, 'named function');
                        if (data.conform[attrib].function === 'regexp') {
                            t.ok(data.conform[attrib].pattern, 'must have pattern');
                            t.ok(typeof data.conform[attrib].field === 'string', 'must reference field');
                            t.ok(data.conform[attrib].replace ? typeof data.conform[attrib].replace === 'string' : true, 'replace is a string');
                        } else if (data.conform[attrib].function === 'join') { 
                            t.ok(Array.isArray(data.conform[attrib].fields), 'must reference fields');
                            t.ok(typeof data.conform[attrib].separator === 'string', 'replace is a string');
                        } else {
                            t.fail(data.conform[attrib].function + ' is not a valid function');
                        }
                    }
                    
                });
                
                //Optional Conform Fields
                t.ok(data.conform.id ? typeof data.conform.id === 'string' : true, "conform - id should be a string");
                t.ok(data.conform.addrtype ? typeof data.conform.addrtype === 'string' : true, "conform - addrtype should be a string");
                t.ok(data.conform.accuracy ? typeof data.conform.accuracy === 'number' : true, "conform - accuracy should be a number");
                t.ok(data.conform.accuracy ? data.conform.accuracy !== 0 : true, "conform - accuracy is not 0");
                t.ok(data.conform.csvsplit ? typeof data.conform.csvsplit === 'string' : true, "conform - csvsplit should be a string");
                t.ok(data.conform.split ? typeof data.conform.split === 'string' : true, "conform - split should be a string");
                t.ok(data.conform.srs ? typeof data.conform.srs === 'string' : true, "conform - srs should be a string");
                t.ok(data.conform.file ? typeof data.conform.file === 'string' : true, "conform - file should be a string");
                t.ok(data.conform.encoding ? typeof data.conform.encoding === 'string' : true, "conform - encoding should be a string");
                t.ok(data.conform.addrtype ? typeof data.conform.addrtype === 'string' : true, "conform - addrtype should be a string");
            }

            //Optional General Fields
            t.ok(data.coverage.email ? typeof data.coverage.email === 'string' : true, "email must be a string");
            t.ok(data.coverage.website ? typeof data.coverage.website === 'string' : true, "website must be a string");
            if (data.coverage.license) {
                if (typeof data.coverage.license === 'string') {
                    t.pass('license supplied as a string [Deprecated]');
                }
                else if (typeof data.coverage.license === 'object') {
                    t.pass('license supplied as an object')
                    ['url', 'text', 'attribution', 'attribution name'].forEach(function(attrib) {
                        if (!data.coverage.license[attrib]) {return;}
                        t.ok(typeof data.coverage.license[attrib] === 'string', "license - " + attrib + " must be a string");
                    });
                }
                else {
                    t.fail("license must be of type string or object");
                }           
        }
        t.end();
        checkSource(++index);
    });
}
