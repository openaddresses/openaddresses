var download = require('./download.js');
var minimist = require('minimist');
var argv = require('minimist')(process.argv.slice(2));
var Step = require('step');

Step(
    function() {
        download(argv, this);
    },
    function(err) {
        process.exit(0);
    }
);
