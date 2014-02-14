var csv = require('csv');
var fs = require('fs');
var path = require('path');
var _ = require('underscore');
var yaml = require('js-yaml');

var header = [];
var states = {};
var keys = [
    'state',
    'city',
    'county',
    'license',
    'year',
    'availability'
];
csv().from.stream(fs.createReadStream(process.argv[2]))
    .on('record', function(row, index){
        if (index == 0) { header = row; return; }
        row = _(row).reduce(function(memo, col, i) {
            if (keys.indexOf(header[i]) === -1) return memo;
            memo[header[i]] = col;
            return memo;
        }, {});
        // Toss all that don't have a URL
        if (row['availability'].trim() != '') {
            var state = row['state'];
            delete row['state'];
            state = state.trim() == '' ? 'General' : state;
            states[state] = states[state] || [];
            states[state].push(row);
        }
    })
    .on('end', function(count){
        var dir = '../' + process.argv[2].split('.')[0];
        try { fs.mkdirSync(dir); } catch(Error) {}
        _(states).each(function(state, key) {
            fs.writeFile(path.join(dir, key + '.yaml'), yaml.safeDump(state));
            console.log('Exported ' + path.join(dir, key + '.yaml'));
        });
    })
    .on('error', function(error){
        console.error(error.message);
    });
