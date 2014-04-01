var test = require('tape').test,
    glob = require('glob'),
    fs = require('fs'),
    queue = require('queue-async'),
    connectors = require('openaddresses-download').connectors,
    request = require('request'),
    Ftp = require('ftp'),
    url = require('url');

var manifest = glob.sync('sources/*.json');
var index = 0;

checkSource(index);

function checkSource(i){
    var source = manifest[i];

    if (i == manifest.lenght-1 || !source) {
        process.exit(0);
    }
    
    test(source, function(t) {
        t.doesNotThrow(function() {
            var data = JSON.parse(fs.readFileSync(source, 'utf8'));
            
            if (data.skip || data.data == undefined) {
                console.log('Skipping Source');
                t.pass();
                t.end();
                checkSource(++index);
            } else {
                if (data.type == "ESRI") {
                    console.log("Testing ESRI");
                    
                    request(data.data + "?f=json", function (error, res, body) {
                        
                        t.notOk(error, "No Error Accessing MapServer");
                        t.ok(res.statusCode == 200, 'Response 200');
                        t.ok(JSON.parse(body).error == undefined, 'Server Online');
                    });

                    t.end();
                    
                } else if (data.type == "ftp") {
                    console.log("Testing FTP");

                    var opt = url.parse(data.data),
                        ftp = new Ftp();

                    opt.user = (opt.auth || ':').split(':')[0];
                    opt.password = (opt.auth || ':').split(':')[1];
                    opt.connTimeout = 5000;

                    ftp.on('ready', function() {
                        
                        ftp.size(opt.path, function(err, size) {
                            if (err){
                                console.log("Invalid FTP Path");
                                t.fail();
                                t.end();
                                ftp.destroy();
                                checkSource(++index);
                            } else {
                                console.log("Connection Established");
                                t.pass();
                                t.end();
                                ftp.destroy();
                                checkSource(++index);
                            }
                        });
                    });

                    ftp.connect(opt);
                } else if (data.type == "http") {
                    console.log("Testing HTTP");
                    connectors[data.type](data, function(err, stream) {
                        t.ok(stream, 'response is good');
                        t.notOk(err, 'no error returned');
                        
                        if (!stream) {
                            checkSource(++index);
                            return t.end()
                        } else {
                            stream.once('error', function(e) {
                                t.fail('server failed: ' + e.message);
                                t.end();
                                stream.removeAllListeners();
                                checkSource(++index);
                            });
                            
                            stream.once('data', function(d) {
                                console.log('Received data');
                                stream.removeAllListeners();
                                stream.destroy(); //HTTP
                                t.end();
                                checkSource(++index);
                            });
                        }
                    });
                } else {
                    t.fail('Incorrect Type');
                    t.end();
                    checkSource(++index);
                }
            }
        }, source + ' is valid json');
    });

}


       
