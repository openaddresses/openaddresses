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

var tapCount = 0;
var tapOK = function(message) {
    console.log('ok ' + (++tapCount) + '\t' + message);
};
var tapNotOK = function(message, diagnostics) {
    console.log(('not ok ' + (++tapCount) + '\t' + message).red);
    diagnostics && console.log(('# ' + diagnostics).red);
};
var tapPlan = function(num, comment) {
    tapCount = 0;
    console.log('1..' + num);
    comment && console.log('# ' + comment);
};

var downloadHTTP = function(address, test, callback) {
    callback = callback || function() {};
    var options = {
        url: address.data,
        timeout: 7000
    };
    (test ? request.head : request.get)(options, function(err, res) {
        if (err) {
            tapNotOK(address.data, err);
            return callback();
        }
        res.statusCode == 200 ?
            tapOK(address.data) :
            tapNotOK(address.data, "HTTP Status " + res.statusCode);
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
                tapNotOK(address.data, err);
                ftp.destroy();
                return callback();
            }
            tapOK(address.data);
            if (test) {
                stream.unref();
                stream.destroy();
                ftp.destroy();
            }
            callback();
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
_(['us', 'canada']).each(function(dir) {
    steps.push(function() {
        var callback = this;
        Step(
            function() {
                fs.readdir('../' + dir, this);
            },
            function(err, files) {
                var group = this.group();
                _(files).each(function(file) {
                    var cb = group();
                    fs.readFile('../' + dir + '/' + file, 'utf8', function(err, data) {
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
                tapPlan(addresses.length, 'Testing directory ../' + dir);
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
})
Step.apply(this, steps);
