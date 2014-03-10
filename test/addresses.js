var test = require('tape').test,
    addresses = require('../');

test('loadMetadata', function(t) {
    var sources = addresses.loadMetadata('sources/*/*', function(err, res) {
        t.equal(err, null);
        t.end();
    });
});

test('downloadAddress', function(t) {
    var sources = addresses.loadMetadata('sources/*/*', function(err, res) {
        t.plan(res.length);
        addresses.loadAddresses(res, function(res) {
            t.notEqual(res, null);
        });
    });
});
