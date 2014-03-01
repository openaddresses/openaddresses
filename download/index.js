var request = require('request');
var url = require('url');
var fs = require('fs');
var minimist = require('minimist');
var _ = require('underscore');
var yaml = require('js-yaml');
var colors = require('colors');
var Ftp = require('ftp');
var Step = require('step');

process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';
var argv = require('minimist')(process.argv.slice(2));

var downloadHTTP = function(address, test, callback) {
    callback = callback || function() {};
    var options = {
        url: address.data,
        timeout: 7000
    };
    (test ? request.head : request.get)(options, function(err, res) {
        if (err) {
            console.log(("ERROR\t" + err + " " + address.data).red);
            return callback();
        }
        res.statusCode == 200 ?
            console.log(res.statusCode + " OK\t" + address.data) :
            console.log((res.statusCode + " ERROR\t" + address.data).red);
        callback();
    }).setMaxListeners(20);
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
                console.log(("FTP\t" + err + " " + address.data).red);
                ftp.destroy();
                return callback();
            }
            console.log("FTP OK\t" + address.data);
            if (test) {
                stream.unref();
                stream.destroy();
                ftp.destroy();
            }
            callback();
        });
    });
    ftp.on('error', function(err) {
        console.log(("FTP\t" + err + " " + address.data).red);
        ftp.destroy();
        callback();
    });
    ftp.connect(opt);
};

var download = function(address, test, callback) {
    callback = callback || function() {};
    if (!address.data) {
        console.log(("NOTICE: No data URL for " + address.website).yellow);
        return callback();
    }
    var options = url.parse(address.data);
    options.protocol == 'ftp:' ?
        downloadFTP(address, test, callback) :
        downloadHTTP(address, test, callback);
};

var downloadFile = function(file, test, callback) {
    callback = callback || function() {};
    fs.readFile(file, 'utf8', function(err, data) {
        if (err) { 
            return callback();
        }
        Step(
            function() {
                var parallel = this.parallel;
                var addresses = yaml.safeLoad(data);
                _(addresses).each(function(address) {
                    download(address, test, parallel());
                });
            },
            callback
        );
    });
};

_(['us', 'canada']).each(function(dir) {
    fs.readdir('../us', function(err, files) {
        var steps = [];
        Step(
            function() {
                var parallel = this.parallel;
                _(files).each(function(file) {
                    downloadFile('../us/' + file, argv['test'], parallel());
                });
            },
            function() {
                process.exit(0);
            }
        );
    });
});
