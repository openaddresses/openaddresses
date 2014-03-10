var test = require('tape').test,
    connectors = require('../connectors');

test('byAddress', function(t) {
    t.equal(connectors.byAddress({
        data: 'http://foo.com/'
    }), connectors.http);

    t.equal(connectors.byAddress({
        data: 'https://foo.com/'
    }), connectors.http);

    t.equal(connectors.byAddress({
        data: 'ftp://foo.com/'
    }), connectors.ftp);

    t.end();
});
