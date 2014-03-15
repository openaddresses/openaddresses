var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    connectors = require('openaddresses-download').connectors;

test('sources', function(t) {
    var sources = glob.sync('sources/*.json');
    t.plan(sources.length);
    sources.forEach(function(source) {
        t.test(source, function(t) {
            t.doesNotThrow(function() {
                var data = JSON.parse(fs.readFileSync(source, 'utf8'));
                if (data.type) {
                    t.ok(connectors[data.type], 'type is valid');
                    if (data.skip) {
                        t.ok(source + 'skipping');
                        t.end();
                    } else { 
                        connectors[data.type](data, function(err, resp) {
                            t.notOk(err, 'response is good');
                            if (resp) resp.end();
                            t.end();
                        });
                    }
                } else {
                    t.ok('has no type or data');
                    t.end();
                }
            }, source + ' is valid json');
        });
    });
});
