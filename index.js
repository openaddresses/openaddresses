var download = require('./addresses.js').download;
var minimist = require('minimist');
var argv = require('minimist')(process.argv.slice(2));
var Step = require('step');
var fs = require('fs');
var path = require('path');

var slug = function(url) {
    var elems = url.split('.');
    var ext = elems.pop();
    if (ext.length > 4) {
        elems.push(ext);
        ext = '';
    } else {
        ext = '.' + ext;
    }
    return elems.join('-').replace(/[^\d^\w]+/g, '-').toLowerCase() + ext;
};
var targetStream = function(url) {
    return fs.createWriteStream(path.join(argv.target, slug(url)));
};

Step(
    function() {
        argv.target ? fs.mkdir(argv.target, this) : this();
    },
    function() {
        var opt = {
            source: argv.source,
            test: argv.test,
            targetStream: targetStream
        };
        download(opt, this);
    },
    function(err) {
        process.exit(0);
    }
);
