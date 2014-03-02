var download = require('./addresses.js').download;
var minimist = require('minimist');
var argv = require('minimist')(process.argv.slice(2));
var Step = require('step');
var fs = require('fs');
var path = require('path');
var _ = require('underscore');

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
var targetStream = function(address) {
    return fs.createWriteStream(path.join(argv.target, slug(address.data)));
};

var reportProgress = function(queue) {
    var clear = function(lines) {
        for (var i = 0; i < lines; i++) {
            // http://ascii-table.com/ansi-escape-sequences-vt-100.php
            process.stdout.write('\u001B[1A\u001B[2K');
        }
    };
    var format = function(f) {
        if (f == undefined) { return 'N/A '; }
        f = Math.round(f*100) + '';
        if (f.length == 1) f = '  ' + f;
        if (f.length == 2) f = ' ' + f;
        return f + '%';
    };
    var ran = false;
    var interval = setInterval(function() {
        ran && clear(queue.size + 2);
        ran = true;
        console.log('Downloads:\t' +
            queue.active.length + ' active\t' +
            queue.jobs.length + ' in queue\t' +
            queue.done + ' done');
        console.log('');
        queue.active;
        for (var i = 0; i < queue.size; i++) {
            if (i < queue.active.length) {
                var download = queue.active[i].obj;
                console.log(format(download.progress()) + " " + download.address.data.substring(0, 76));
            } else {
                console.log(' ');
            }
        }
        !queue.active.length && clearInterval(interval);
    }, 100);
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
        var queue = download(opt, this);
        !argv.test && reportProgress(queue);
    },
    function(err) {
        // Bail out hard. Some sockets appear not to close out cleanly.
        process.exit(0);
    }
);
