var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs');

var manifest = glob.sync('sources/*.json');
var index = 0;

checkSource(index);

function checkSource(i){
    var source = manifest[i];

    if (i == manifest.lenght-1 || !source) {
        process.exit(0);
    }
    
    test(source, function(t) {
        t.doesNotThrow(function() {
            var data = JSON.parse(fs.readFileSync(source, 'utf8'));
            
            if (data.skip || data.data === undefined) {
                console.log('[WARN] Skip flag Detected!');
            }

            t.ok(data.data, "Data URL Included");

            t.ok(data.type, "Data URL Type Included");

            t.ok(data.coverage, "Data Coverage Included");

            t.pass('Incorrect Type');
            t.end();
            checkSource(++index);
        }, source + ' is valid json');
    });



}
