var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    request = require('request');
    validator = require('validator');
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

    if (i == manifest.lenght-1 || !source) {process.exit(0);}

    test(source, function(t) {
        var raw = fs.readFileSync(source, 'utf8');
        var data = validateJSON(raw);

        t.ok(data, "Data should be valid JSON");

        if (data) {
            if (data.skip) {t.pass("WARN - Skip Flag Detected");}

            // Ensure people don't make up tags
            legalTags = [
                // https://github.com/openaddresses/openaddresses/blob/master/CONTRIBUTING.md#core-tags
                'data', 'type', 'coverage', 'coverage', 'conform', 'compression',
                
                // https://github.com/openaddresses/openaddresses/blob/master/CONTRIBUTING.md#optional-tags
                'website', 'license', 'note', 'attribution', 'email', 'language',
                
                // Not documented, but works
                'year', 'skip'
                ];

            Object.keys(data).forEach(function (userTag) {
                t.ok(legalTags.indexOf(userTag) !== -1, '"'+userTag+'" is not a tag documented in CONTRIBUTING.md.');
            });

            //Mandatory Fields & Coverage
            t.ok(data.data, "Should be data");
            t.ok(data.type, "Should be a type");
            if (data.compression && ['zip'].indexOf(data.compression) === -1) {t.fail("Should be a supported compression type");}
            t.ok(typeof data.coverage === 'object', "Should have a Coverage Object");
            t.ok(typeof data.coverage.country === 'string', "Country coverage should be a string");
            t.ok(data.coverage.province ? typeof data.coverage.country === 'string' : true, "Province coverage should be a string");
            t.ok(data.coverage.county ? typeof data.coverage.county === 'string' : true, "County coverage should be a string");
            t.ok(data.coverage.city ? typeof data.coverage.city === 'string' : true, "City coverage should be a string");
            t.ok(['http', 'ftp', 'esri'].indexOf(data.type.toLowerCase()) !== -1, "Should be a valid type");

            if (data.conform) {
                //Ensure people don't make up new values
                var conformOptions = [
                    'type', 'csvsplit', 'split', 'srs',
                    'file', 'encoding', 'headers', 'skiplines', 'lon', 'lat',
                    'number', 'street', 'unit', 'city', 'postcode', 'district',
                    'region', 'addrtype', 'notes', 'accuracy', 'id'
                    ];
                Object.keys(data.conform).forEach(function (conformKey) {
                    t.ok(conformOptions.indexOf(conformKey) !== -1, 'conform - "' + conformKey + '" is not a recognized attribute tag');
                });

                //Mandatory Conform Fields
                t.ok(data.conform.type && typeof data.conform.type === 'string', "Conform should have a type attribute");
                t.ok(['gdb', 'shapefile', 'shapefile-polygon', 'csv', 'geojson', 'xml'].indexOf(data.conform.type) !== -1, "Conform should have a supported type");
                if (data.conform.type === 'csv') {
                    t.ok(data.conform.hasOwnProperty('lon'), "conform - lon attribute required for type csv");
                    t.ok(data.conform.hasOwnProperty('lat'), "conform - lat attribute required for type csv");
                } else {
                    t.ok(!data.conform.hasOwnProperty('lon'), 'lon should only be set for csv type');
                    t.ok(!data.conform.hasOwnProperty('lat'), 'lat should only be set for csv type');
                }
                t.ok(data.conform.hasOwnProperty('number'), "conform - number attribute required");
                t.ok(data.conform.hasOwnProperty('street'), "conform - street attribute required");

                //Conform Attributes
                ['lat', 'lon', 'number', 'street', 'unit', 'city', 'postcode', 'district', 'region', 'notes', 'id'].forEach(function(attrib) {
                    if (!data.conform[attrib]) { return; }
                    if (typeof data.conform[attrib] === 'string') {
                        t.ok(data.conform[attrib], attrib + ' should not be an empty string');
                    } else if (Array.isArray(data.conform[attrib])) {
                        t.ok(data.conform[attrib].length >= 1, attrib + ' merge array should have at least one element');
                    } else if (typeof data.conform[attrib] === 'object') {
                        t.ok(data.conform[attrib].function, attrib + ' should name a function');
                        if (data.conform[attrib].function === 'regexp') {
                            t.ok(data.conform[attrib].pattern, attrib + ' regexp should have pattern');
                            t.ok(typeof data.conform[attrib].field === 'string', attrib + ' regexp should reference a field');
                            t.ok(data.conform[attrib].replace ? typeof data.conform[attrib].replace === 'string' : true, attrib + ' regexp replace should be a string');
                        } else if (data.conform[attrib].function === 'join') { 
                            t.ok(Array.isArray(data.conform[attrib].fields), attrib + ' join should reference fields');
                            t.ok(typeof data.conform[attrib].separator === 'string', attrib + ' join separator should be a string');
                        } else if (data.conform[attrib].function === 'format') {
                            t.ok(Array.isArray(data.conform[attrib].fields), attrib + ' format should reference fields');
                            t.ok(typeof data.conform[attrib].format === 'string', attrib + ' format should be a string');
                        } else {
                            t.fail(data.conform[attrib].function + ' function should be valid');
                        }
                    }
                    
                });
                
                //Optional Conform Fields
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
            if (data.email) {
                t.ok(typeof data.email === 'string',"email must be a string");
                t.ok(validator.isEmail(data.email),"email must be a valid email address");
            }
            if (data.website) {
                t.ok(typeof data.website === 'string',"website must be a string");
                t.ok(validator.isURL(data.website),"website must be a valid URL");
            }
            if (data.license) {
                if (typeof data.license === 'string') {
                    t.pass('license supplied as a string [Deprecated]');
                }
                else if (typeof data.license === 'object') {
                    t.pass('license supplied as an object');
                    ['url', 'text', 'attribution name'].forEach(function(attrib) {
                        if (!data.license[attrib]) {return;}
                        t.ok(typeof data.license[attrib] === 'string', "license - " + attrib + " must be a string");
                        });
                    t.ok(data.license.url ? validator.isURL(data.license.url) : true, "license - url must be a valid URL");
                    t.ok(data.license.attribution ? typeof data.license.attribution === 'boolean' : true, "license - attribution must be boolean");
                    t.ok(data.license['share-alike'] ? typeof data.license['share-alike'] === 'boolean' : true, "license - share-alike must be boolean");
                }
                else {
                    t.fail("license must be of type string or object");
                }           
            }
        }
        t.end();
        checkSource(++index);
    });
}
