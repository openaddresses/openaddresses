var Ftp = require('ftp');
var http = require('http');
var _ = require('underscore');
var url = require('url');

process.env.NODE_TLS_REJECT_UNAUTHORIZED = '0';
var connectors = module.exports = {};

connectors.http = function(address, callback) {
    return http.request({
        uri: address
    }, callback);
};

connectors.ftp = function(address, targetStream) {
    var opt = url.parse(address.data);
    opt.user = (opt.auth || ':').split(':')[0];
    opt.password = (opt.auth || ':').split(':')[1];
    opt.connTimeout = 5000;
    var size;
    var downloaded = 0;
    var started = 0;
    var FTP = {};
    FTP.address = address;
    FTP.download = function(test, callback) {
        if (_(test).isFunction()) {
            callback = test;
            test = false;
        }
        callback = callback || function() {};
        var ftp = new Ftp();
        ftp.on('ready', function() {
            ftp.size(opt.path, function(err, sz) {
                size = sz;
                ftp.get(opt.path, function(err, stream) {
                    if (err) {
                        ftp.destroy();
                        return callback(err);
                    }
                    if (test) {
                        stream.unref();
                        stream.destroy();
                        ftp.destroy();
                        callback();
                    } else {
                        started = Date.now();
                        targetStream && stream.pipe(targetStream(address));
                        stream.on('data', function(buf) {
                            downloaded += buf.length;
                        });
                        stream.on('end', callback);
                    }
                });
            });
        });
        ftp.on('error', function(err) {
            ftp.destroy();
            callback(err);
        });
        ftp.connect(opt);
    };
    FTP.test = function(callback) {
        FTP.download(true, callback);
    };
    FTP.progress = function() {
        return size ? downloaded / size : undefined;
    };
    FTP.rate = function() {
        return downloaded && started ? downloaded / ((Date.now() - started) / 1000) : undefined;
    };
    return FTP;
};

connectors.esri = function(address, targetStream) {
    // Downloads for esri not implemented yet.
    return connectors.http(address, null);
};

connectors.byAddress = function(address, targetStream) {
    var opt = url.parse(address.data);
    var connector;
    if (opt.protocol == 'ftp:') {
        connector = connectors.ftp;
    } else if (opt.protocol == 'http:' || opt.protocol == 'https:') {
        if (opt.path.search(/\/MapServer\/\d+/) !== -1) {
            connector = connectors.esri;
        } else if (opt.path.search(/\/FeatureServer\/\d+$/) !== -1) {
            connector = connectors.esri;
        } else {
            connector = connectors.http;
        }
    }
    if (!connector) throw Error('No connector found', address);
    return connector;
};
