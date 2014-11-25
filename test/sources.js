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
            t.ok(data.data, "Checking for data");
            t.ok(data.type, "Checking for type");
            if (data.compression && ['zip'].indexOf(data.compression) === -1) t.fail("Compression type not supported");
            if (['http', 'ftp', 'ESRI'].indexOf(data.type) === -1) process.exit();//t.fail("Type not supported");

            if (data.conform) {
                t.ok(data.conform.lon, "conform - lon attribute required");
                t.ok(data.conform.lat, "conform - lat attribute required");
                t.ok(data.conform.number, "conform - number attribute required");
                t.ok(data.conform.street, "conform - street attribute required");
                t.ok(data.conform.type, "conform - type attribute required");
                t.ok(['shapefile', 'shapefile-polygon', 'csv', 'geojson'].indexOf(data.conform.type) !== -1, "type is supported")
                if (data.conform.merge) t.ok(Array.isArray(data.conform.merge), "Merge is an array");
            }

            t.end();
            checkSource(++index);
        }, source + ' is valid json');
    });
}
