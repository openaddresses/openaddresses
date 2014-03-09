var fs = require('fs');
var _ = require('underscore');
var yaml = require('js-yaml');
var Step = require('step');
var glob = require('glob');
var connectors = require('./connectors.js')
require('colors');

// Simple job queue.
var queue = function(size) {
    var q = {};
    q.jobs = [];
    q.active = [];
    q.done = 0;
    q.size = size;
    var interval = null;
    var work = function() {
        if (interval) return;
        interval = setInterval(function() {
            while (q.active.length < size && q.jobs.length) {
                (function() {
                    var job = q.jobs.shift();
                    q.active.push(job);
                    job.func.call(job.obj, function() {
                        q.active = _(q.active).without(job);
                        q.done++;
                        job.callback.apply(null, arguments);
                    });
                })();
            }
            !q.jobs.length && !q.active.length && clearInterval(interval);
        }, 10);
    };
    q.add = function(obj, func, callback) {
        q.jobs.push({obj: obj, func: func, callback: callback});
        work();
    };
    return q;
};

// Helper for TAP test outputs.
var tap = function(num, comment) {
    console.log('1..' + num);
    comment && console.log('# ' + comment);
    tap = {};
    var count = 0;
    tap.OK = function(message) {
        console.log(('ok ' + (count++) + '\t').green + message.grey);
    };
    tap.notOK = function(message, diagnostics) {
        console.log(('not ok ' + (count++) + '\t').red + message.grey);
        diagnostics && console.log(('# ' + diagnostics).grey);
    };
    return tap;
};

var download = function(options, callback) {
    process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';

    var dlQueue = queue(20);
    var download = function(address, test, callback) {
        callback = callback || function() {};
        if (!address.data) {
            return callback("No data URL for " + address.website);
        }
        var connector = connectors.byAddress(address)(address, options.targetStream, test);
        dlQueue.add(connector, test ? connector.test : connector.download, callback);
    };

    Step(
        function(err) {
            if (err) console.error(err.toString().red);
            glob(options.source, this);
        },
        function(err, files) {
            if (err) console.error(err.toString().red);
            var group = this.group();
            _(files).each(function(file) {
                var cb = group();
                fs.readFile(file, 'utf8', function(err, data) {
                    cb(err, yaml.safeLoad(data));
                });
            });
        },
        function(err, addresses) {
            if (err) console.error(err.toString().red);
            var group = this.group();
            addresses = _(addresses).reduce(function(memo, address) {
                memo = memo.concat(address);
                return memo;
            }, []);
            var test = options.test ?
                tap(addresses.length, 'Testing ' + options.source) :
                null;
            _(addresses).each(function(address) {
                var cb = group();
                cb = _(cb).wrap(function(cb, err) {
                    test && (err ? test.notOK : test.OK)(address.data || address.website, err);
                    cb();
                });
                process.nextTick(function() {
                    download(address, test, cb);
                });
            });
        },
        callback
    );
    return dlQueue;
};

module.exports = {
    download: download
};
