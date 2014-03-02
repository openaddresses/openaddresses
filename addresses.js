var request = require('request');
var url = require('url');
var fs = require('fs');
var _ = require('underscore');
var yaml = require('js-yaml');
var Ftp = require('ftp');
var Step = require('step');
var glob = require('glob');
require('colors');

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

var download = function(options, callback) {
    process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';

    var tapOK = function(message) {
        console.log('ok\t'.green + message.grey);
    };
    var tapNotOK = function(message, diagnostics) {
        console.log('not ok\t'.red + message.grey);
        diagnostics && console.log(('# ' + diagnostics).grey);
    };
    var tapPlan = function(num, comment) {
        console.log('1..' + num);
        comment && console.log('# ' + comment);
    };

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
                tapOK(address.data);
                !test && req.pipe(options.targetStream(address));
            } else {
                tapNotOK(address.data, res.statusCode);
            }
        });
        req.on('error', function(err) {
            tapNotOK(address.data, err);
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
                    tapNotOK(address.data, err);
                    ftp.destroy();
                    return callback();
                }
                tapOK(address.data);
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
            tapNotOK(address.data, err);
            ftp.destroy();
            callback();
        });
        ftp.connect(opt);
    };

    var dlQueue = queue(20);
    var download = function(address, test, callback) {
        callback = callback || function() {};
        if (!address.data) {
            tapOK("# SKIP - no data URL for " + address.website);
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
            tapPlan(addresses.length, 'Testing ' + options.source);
            _(addresses).each(function(address) {
                var cb = group();
                process.nextTick(function() {
                    download(address, options.test, cb);
                });
            });
        },
        callback
    );
};

module.exports = {
    download: download
};
