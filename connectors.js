var request = require('request');
var Ftp = require('ftp');
var _ = require('underscore');
var url = require('url');

var connectors = module.exports = {};

connectors.http = function(address, targetStream, test) {
    var opt = {
        url: address.data,
        timeout: 7000
    };
    var size;
    var downloaded = 0;
    var started = 0;
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
                    started = Date.now();
                    req.pipe(targetStream(address));
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
    HTTP.rate = function() {
        return downloaded && started ? downloaded / ((Date.now() - started) / 1000) : undefined;
    };
    return HTTP;
};

connectors.ftp = function(address, targetStream, test) {
    var opt = url.parse(address.data);
    opt.user = (opt.auth || ':').split(':')[0];
    opt.password = (opt.auth || ':').split(':')[1];
    opt.connTimeout = 5000;
    var size;
    var downloaded = 0;
    var started = 0;
    var FTP = {};
    FTP.address = address;
    FTP.download = function(callback) {
        callback = callback || function() {};
        var ftp = new Ftp();
        ftp.on('ready', function() {
            ftp.size(opt.path, function(err, sz) {
                size = sz;
                ftp.get(opt.path, function(err, stream) {
                    if (err) {
                        test && test.notOK(address.data, err);
                        ftp.destroy();
                        return callback();
                    }
                    if (test) {
                        test.OK(address.data);
                        stream.unref();
                        stream.destroy();
                        ftp.destroy();
                        callback();
                    } else {
                        started = Date.now();
                        stream.pipe(targetStream(address));
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
    FTP.rate = function() {
        return downloaded && started ? downloaded / ((Date.now() - started) / 1000) : undefined;
    };
    return FTP;
};
