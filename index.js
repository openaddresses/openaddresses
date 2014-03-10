var fs = require('fs');
var yaml = require('js-yaml');
var glob = require('glob');
var queue = require('queue-async');
var stream = require('stream');
var connectors = require('./connectors.js');

module.exports.loadMetadata = loadMetadata;
module.exports.loadAddresses = loadAddresses;
    
function loadMetadata(source, callback) {
    glob(source, parseFiles);
    function parseFiles(err, files) {
        if (err) return console.error(err.toString());
        var q = queue(1);

        files.forEach(function(file) {
            q.defer(fs.readFile, file, 'utf8');
        });

        q.awaitAll(function(err, res) {
            if (err) return console.error(err.toString());
            callback(null, res.map(function(_) {
                return yaml.safeLoad(_);
            }));
        });
    }
}

function loadAddresses(addresses, callback) {
    var q = queue(10);
    addresses.reduce(function(memo, address) {
        memo = memo.concat(address);
        return memo;
    }, []).forEach(function(address) {
        if (!address.data) {
            return callback('No data URL for ' + address.website);
        }
        q.defer(connectors.byAddress(address), address);
    });
    q.awaitAll(callback);
}
