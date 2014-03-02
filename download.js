var request = require('request');
var url = require('url');
var fs = require('fs');
var _ = require('underscore');
var yaml = require('js-yaml');
var Ftp = require('ftp');
var Step = require('step');
var glob = require('glob');
var path = require('path');
require('colors');

module.exports =
function(opt, callback) {
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
    var targetStream = function(url) {
        return fs.createWriteStream(path.join(opt.target, + slug(url)));
    };

    var downloadHTTP = function(address, test, callback) {
        // Wrap in _.once as on('error') and on('end') are not called
        // consistently either both or alternatively.
        callback = _.once(callback || function() {});
        var options = {
            url: address.data,
            timeout: 7000
        };
        var req = (test ? request.head : request.get)(options);
        req.setMaxListeners(20);
        req.on('response', function(res) {
            if (res.statusCode == 200) {
                tapOK(address.data);
                !test && req.pipe(targetStream(address.data));
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
                    stream.pipe(fs.createWriteStream('data/' + slug(address.data)));
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

    Step(
        function() {
            opt.target ? fs.mkdir(opt.target, this) : this();
        },
        function(err) {
            if (err) console.error(err.toString().red);
            glob(opt.source, this);
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
            tapPlan(addresses.length, 'Testing ' + opt.source);
            _(addresses).each(function(address) {
                var cb = group();
                process.nextTick(function() {
                    download(address, opt.test, cb);
                });
            });
        },
        callback
    );
};
