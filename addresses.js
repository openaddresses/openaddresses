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

    var HTTP = function(address, test) {
        var opt = {
            url: address.data,
            timeout: 7000
        };
        var size;
        var downloaded = 0;
        var HTTP = {};
        HTTP.address = address;
        HTTP.download = function(callback) {
            // Wrap in _.once as on('error') and on('end') are not called
            // consistently either both or alternatively.
            callback = _.once(callback || function() {});
            var req = (test ? request.head : request.get)(opt);
            req.setMaxListeners(20);
            req.on('response', function(res) {
                if (res.statusCode == 200) {
                    if (test) {
                        test.OK(address.data);
                    } else {
                        try { size = parseInt(res.headers['content-length']); } catch(e) {};
                        req.pipe(options.targetStream(address));
                        req.on('data', function(buf) {
                            downloaded += buf.length;
                        });
                    }
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
        HTTP.progress = function() {
            return size ? downloaded / size : undefined;
        };
        return HTTP;
    };

    var FTP = function(address, test) {
        var opt = url.parse(address.data);
        opt.user = (opt.auth || ':').split(':')[0];
        opt.password = (opt.auth || ':').split(':')[1];
        opt.connTimeout = 5000;
        var size;
        var downloaded = 0;
        var FTP = {};
        FTP.address = address;
        FTP.download = function(callback) {
            callback = callback || function() {};
            var ftp = new Ftp();
            ftp.on('ready', function() {
                ftp.size(opt.path, function(err, size) {
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
                            var downloaded = 0;
                            stream.on('data', function(buf) {
                                downloaded += buf.length;
                            });
                            stream.on('end', callback);
                        }
                    });
                });
            });
            ftp.on('error', function(err) {
                test && test.notOK(address.data, err);
                ftp.destroy();
                callback();
            });
            ftp.connect(opt);
        };
        FTP.progress = function() {
            return size ? downloaded / size : undefined;
        };
        return FTP;
    };

    var dlQueue = queue(20);
    var download = function(address, test, callback) {
        callback = callback || function() {};
        if (!address.data) {
            test && test.OK("# SKIP - no data URL for " + address.website);
            return callback();
        }
        var options = url.parse(address.data);
        var downloader= options.protocol == 'ftp:' ?
            FTP(address, test) :
            HTTP(address, test);
        dlQueue.add(downloader, downloader.download, callback);
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
    return dlQueue;
};

module.exports = {
    download: download
};
