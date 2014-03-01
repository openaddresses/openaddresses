var request = require('request');
var url = require('url');
var fs = require('fs');
var minimist = require('minimist');
var _ = require('underscore');
var yaml = require('js-yaml');
var colors = require('colors');
var Ftp = require('ftp');

process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';
var argv = require('minimist')(process.argv.slice(2));

var downloadHTTP = function(address, test) {
    (test ? request.head : request.get)(address.data, function(err, res) {
        if (err) {
            console.log(("ERROR\t" + err + " " + address.data).red);
            return;
        }
        res.statusCode == 200 ?
            console.log(res.statusCode + " OK\t" + address.data) :
            console.log((res.statusCode + " ERROR\t" + address.data).red);
    }).setMaxListeners(20);
};

var downloadFTP = function(address, test) {
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
                return;
            }
            console.log("FTP OK\t" + address.data);
            if (test) {
                ftp.destroy();
            }
        });
    });
    ftp.on('error', function(err) {
        console.log(("FTP\t" + err + " " + address.data).red);
        ftp.destroy();
    });
    ftp.connect(opt);
};

var download = function(address, test) {
    var options = url.parse(address.data);
    options.protocol == 'ftp:' ?
        downloadFTP(address, test) :
        downloadHTTP(address, test);
};

var downloadFile = function(file, test) {
    fs.readFile(file, 'utf8', function(err, data) {
        if (err) { 
            return;
        }
        var addresses = yaml.safeLoad(data);
        _(addresses).each(function(address) {
            download(address, test);
        });
    });
};

_(['us', 'canada']).each(function(dir) {
    fs.readdir('../us', function(err, files) {
        _(files).each(function(file) {
            downloadFile('../us/' + file, argv['test']);
        });
    });
});
