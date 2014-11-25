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
            t.ok(data.data, "Checking for data in " + source);

            t.end();
            checkSource(++index);
        }, source + ' is valid json');
    });
}
