var request = require('request');
var url = require('url');
var fs = require('fs');
var minimist = require('minimist');
var _ = require('underscore');
var yaml = require('js-yaml');
var colors = require('colors');
var Ftp = require('ftp');
var Step = require('step');
var glob = require('glob');

process.env['NODE_TLS_REJECT_UNAUTHORIZED'] = '0';
var argv = require('minimist')(process.argv.slice(2));

var tapOK = function(message) {
    console.log('ok\t' + message);
};
var tapNotOK = function(message, diagnostics) {
    console.log(('not ok\t' + message).red);
    diagnostics && console.log(('# ' + diagnostics).red);
};
var tapPlan = function(num, comment) {
    console.log('1..' + num);
    comment && console.log('# ' + comment);
};

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

var downloadHTTP = function(address, test, callback) {
    callback = callback || function() {};
    var options = {
        url: address.data,
        timeout: 7000
    };
    var req = (test ? request.head : request.get)(options);
    req.setMaxListeners(20);
    req.on('response', function(res) {
        if (res.statusCode == 200) {
            tapOK(address.data);
            !test && req.pipe(fs.createWriteStream('../data/' + slug(address.data)));
        } else {
            tapNotOK(address.data, res.statusCode);
        }
    });
    req.on('error', function(err) {
        tapNotOK(address.data, err);
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
                stream.pipe(fs.createWriteStream('../data/' + slug(address.data)));
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

var download = function(address, test, callback) {
    callback = callback || function() {};
    if (!address.data) {
        tapOK("# SKIP - no data URL for " + address.website);
        return callback();
    }
    var options = url.parse(address.data);
    options.protocol == 'ftp:' ?
        downloadFTP(address, test, callback) :
        downloadHTTP(address, test, callback);
};

var steps = [];
_(['../canada/*', '../us/*']).each(function(path) {
    steps.push(function() {
        var callback = this;
        Step(
            function() {
                glob(path, this);
            },
            function(err, files) {
                var group = this.group();
                _(files).each(function(file) {
                    var cb = group();
                    fs.readFile(file, 'utf8', function(err, data) {
                        cb(err, yaml.safeLoad(data));
                    });
                });
            },
            function(err, addresses) {
                var parallel = this.parallel;
                addresses = _(addresses).reduce(function(memo, address) {
                    memo = memo.concat(address);
                    return memo;
                }, []);
                tapPlan(addresses.length, 'Testing ' + path);
                _(addresses).each(function(address) {
                    download(address, argv['test'], parallel());
                });
            },
            callback
        );
    });
});
steps.push(function() {
    process.exit(0);
});
Step.apply(this, steps);
