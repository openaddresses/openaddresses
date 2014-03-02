var request = require('request');
var url = require('url');
var fs = require('fs');
var _ = require('underscore');
var yaml = require('js-yaml');
var Ftp = require('ftp');
var Step = require('step');
var glob = require('glob');
require('colors');

// Simple job queue.
var queue = function(len) {
    var jobs = [];
    var active = [];
    var interval = null;
    var work = function() {
        if (interval) return;
        interval = setInterval(function() {
            while (active.length < len && jobs.length) {
                (function() {
                    var job = jobs.shift();
                    active.push(job);
                    job.func(function() {
                        active = _(active).without(job);
                        job.callback.apply(null, arguments);
                    });
                })();
            }
            !jobs.length && !active.length && clearInterval(interval);
        }, 10);
    };
    return function(func, callback) {
        jobs.push({func: func, callback: callback});
        work();
    };
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

    var downloadHTTP = function(address, test, callback) {
        // Wrap in _.once as on('error') and on('end') are not called
        // consistently either both or alternatively.
        callback = _.once(callback || function() {});
        var opt = {
            url: address.data,
            timeout: 7000
        };
        var req = (test ? request.head : request.get)(opt);
        req.setMaxListeners(20);
        req.on('response', function(res) {
            if (res.statusCode == 200) {
                test && test.OK(address.data);
                !test && req.pipe(options.targetStream(address));
            } else {
                test && test.notOK(address.data, res.statusCode);
            }
        });
        req.on('error', function(err) {
            test && test.notOK(address.data, err);
            callback();
        });
        req.on('end', callback);
    };

    var downloadFTP = function(address, test, callback) {
        callback = callback || function() {};
        var ftp = new Ftp();
        var opt = url.parse(address.data);
        opt.user = (opt.auth || ':').split(':')[0];
        opt.password = (opt.auth || ':').split(':')[1];
        opt.connTimeout = 5000;
        ftp.on('ready', function() {
            ftp.get(opt.path, function(err, stream) {
                if (err) {
                    test && test.notOK(address.data, err);
                    ftp.destroy();
                    return callback();
                }
                test && test.OK(address.data);
                if (test) {
                    stream.unref();
                    stream.destroy();
                    ftp.destroy();
                    callback();
                } else {
                    stream.pipe(options.targetStream(address));
                    stream.on('end', callback);
                }
            });
        });
        ftp.on('error', function(err) {
            test && test.notOK(address.data, err);
            ftp.destroy();
            callback();
        });
        ftp.connect(opt);
    };

    var dlQueue = queue(20);
    var download = function(address, test, callback) {
        callback = callback || function() {};
        if (!address.data) {
            test && test.OK("# SKIP - no data URL for " + address.website);
            return callback();
        }
        var options = url.parse(address.data);
        dlQueue(function(callback) {
            options.protocol == 'ftp:' ?
                downloadFTP(address, test, callback) :
                downloadHTTP(address, test, callback);
        }, callback);
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
                process.nextTick(function() {
                    download(address, test, cb);
                });
            });
        },
        callback
    );
};

module.exports = {
    download: download
};
