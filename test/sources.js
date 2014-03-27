var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    queue = require('queue-async'),
    connectors = require('openaddresses-download').connectors;

var q = queue(1);

glob.sync('sources/*.json').forEach(function(source) {
    q.defer(function(source, callback) {
        test(source, function(t) {
            t.doesNotThrow(function() {
                var data = JSON.parse(fs.readFileSync(source, 'utf8'));
                if (data.type) {
                    if (data.type = "ESRI") {
                        t.ok('Ignoring ESRI type - skipping');
                        t.end();
                        callback();
                    } else
                        t.ok(connectors[data.type], 'type is valid');
                        
                        if (data.skip) {
                            t.ok(source + 'skipping');
                            t.end();
                            callback();
                        } else {
                            connectors[data.type](data, function(err, resp) {
                                t.ok(resp, 'response is good');
                                t.notOk(err, 'no error returned');
                                if (!resp) {
                                    callback();
                                    return t.end();
                                }
                                resp.once('error', function(e) {
                                    t.fail('server failed: ' + e.message);
                                    resp.end();
                                    t.end();
                                    callback();
                                });
                                resp.once('data', function(d) {
                                    t.pass('received data');
                                    t.end();
                                    resp.end();
                                    callback();
                                });
                            });
                        }
                    }
                } else {
                    t.ok('has no type or data');
                    t.end();
                    callback();
                }
            }, source + ' is valid json');
        });
    }, source);
});
