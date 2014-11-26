var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs');

var manifest = glob.sync('sources/*.json');
var index = 0;

checkSource(index);

function checkSource(i){
    var source = manifest[i];

    if (i == manifest.lenght-1 || !source) process.exit(0);

    test(source, function(t) {
        t.doesNotThrow(function() {
            var data = JSON.parse(fs.readFileSync(source, 'utf8'));
            if (data.skip) t.pass("WARN - Skip Flag Detected");

            //Mandatory Fields & Coverage
            t.ok(data.data, "Checking for data");
            t.ok(data.type, "Checking for type");
            if (data.compression && ['zip'].indexOf(data.compression) === -1) t.fail("Compression type not supported");
            t.ok(typeof data.coverage === 'object', "Coverage Object Exists");
            t.ok(typeof data.coverage.country === 'string');
            t.ok(data.coverage.province ? typeof data.coverage.country === 'string' : true, "coverage - Province must be a string");
            t.ok(data.coverage.county ? typeof data.coverage.county === 'string' : true, "coverage - County must be a string");
            t.ok(data.coverage.city ? typeof data.coverage.city === 'string' : true, "coverage - City must be a string");
            t.notok(data.coverage.city && data.coverage.county, "City and County not used together");
            t.ok(['http', 'ftp', 'ESRI'].indexOf(data.type) !== -1, "Type valid");

            if (data.conform) {
                //Mandator Conform Fields
                t.ok(data.conform.lon && typeof data.conform.lon === 'string', "conform - lon attribute required");
                t.ok(data.conform.lat && typeof data.conform.lat === 'string', "conform - lat attribute required");
                t.ok(data.conform.number && typeof data.conform.number === 'string', "conform - number attribute required");
                t.ok(data.conform.street && typeof data.conform.street === 'string', "conform - street attribute required");
                t.ok(data.conform.type && typeof data.conform.type === 'string', "conform - type attribute required");
                t.ok(['shapefile', 'shapefile-polygon', 'csv', 'geojson'].indexOf(data.conform.type) !== -1, "conform - type is supported");

                //Optional Conform Fields
                t.ok(data.conform.merge ? Array.isArray(data.conform.merge) : true, "conform - Merge is an array");
                t.ok(data.conform.csvsplit ? typeof data.conform.csvsplit === 'string' : true, "conform - csvsplit is a string");
                t.ok(data.conform.split ? typeof data.conform.split === 'string' : true, "conform - split is a string");
                t.ok(data.conform.srs ? typeof data.conform.srs === 'string' : true, "conform - srs is a string");
                t.ok(data.conform.file ? typeof data.conform.file === 'string' : true, "conform - file is a string");
                t.ok(data.conform.charset ? typeof data.conform.charset === 'string' : true, "conform - charset is a string");
                t.ok(data.conform.headers ? typeof data.conform.headers === 'string' : true, "conform - headers is a string");

            }

            t.end();
            checkSource(++index);
        }, source + ' is valid json');
    });
}
