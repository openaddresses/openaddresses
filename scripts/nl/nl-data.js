/*jslint indent: 4, node: true */

//---- Settings ----
//Must be Initialized With PostGIS
var connect = "postgres://postgres@localhost/nl";
//------------------

var pg = require('pg'),
    fs = require('fs'),
    xmlStream = require('node-expat'),
    req = require('http'),
    sh = require('execSync'),
    flow = require('flow'),
    async = require('async');

var db = new pg.Client(connect);

var xml;
var type = process.argv[2];

//Skips to process a specific type
//All folders/postgres tables must
//be setup manually
if (type) {
    switch (type) {
        case 'NUM': //Numbers
            importNUM();
            break;
        case 'WPL': //Cities
            importWPL();
            break;
        case 'OPR': //Streets
            importOPR();
            break;
        case 'LIG': //Berths
            importLIG();
            break;
        case 'PND': //Buildings
            importPND();
            break;
        case 'STA': //Stands
            importSTA();
            break;
        case 'VBO': //Accomadations
            importVBO();
            break;
        case 'SQL': //Skip to SQL
            SQLsetup();
            break;
        case 'OA':
            genPoints();
            break;
        case 'CSV':
            makeCSV();
            break;
        default:
            console.log("Not a Valid Arg");
            process.exit(1);
            break;
    }
} else {
    fs.mkdir('./tmp', function(err) {
        if (err) console.log("Folder Exists");
        download();
    });
}

function download() {
    console.log("Commencing Download");
    var file = fs.createWriteStream('./tmp/nl-address.zip');
    var request = req.get("http://gis-data.s3.amazonaws.com/nl-gov/inspireadressen.zip", function(response) {
        response.pipe(file);
    });
    request.on('error', function(err) {
        throw new Error('Failed to Download File');
    });

    file.on('error', function(err) {
        throw new Error('Failed to Save File');
    });

    file.on('close', function(err) {
        console.log("Download Complete");
        decompress();
    });
}

function decompress() {
    console.log("Decompressing File");
    var code = sh.run('unzip -d ./tmp/ ./tmp/nl-address.zip');
    if (code !== 0) throw new Error('Could Not nl-address');
    code = sh.run('unzip -a -d ./tmp/num/ ./tmp/9999NUM08042014.zip');
    if (code !== 0) throw new Error('Could Not Unzip NUM');
    code = sh.run('unzip -a -d ./tmp/wpl/ ./tmp/9999WPL08042014.zip');
    if (code !== 0) throw new Error('could not umzip WPL');
    code = sh.run('unzip -a -d ./tmp/opr/ ./tmp/9999OPR08042014.zip');
    if (code !== 0) throw new Error('could not umzip OPR');
    code = sh.run('unzip -a -d ./tmp/pnd/ ./tmp/9999PND08042014.zip');
    if (code !== 0) throw new Error('could not umzip PND');
    code = sh.run('unzip -a -d ./tmp/vbo/ ./tmp/9999VBO08042014.zip');
    if (code !== 0) throw new Error('could not umzip VBO');
    code = sh.run('unzip -a -d ./tmp/sta/ ./tmp/9999STA08042014.zip');
    if (code !== 0) throw new Error('could not umzip STA');
    code = sh.run('unzip -a -d ./tmp/lig/ ./tmp/9999LIG08042014.zip');
    if (code !== 0) throw new Error('could not umzip LIG');
    SQLsetup();
}

function SQLsetup() {
    pg.connect(connect, function(err, client, done) {
        if (err) throw new Error ("Unable to Connect to postgresql");

        console.log("Creating Database");

        var queue = [];

        queue.push(db.query.bind(client, "CREATE TABLE nlNum (num text, postcode text, id text, placeid text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlCity (id text, name text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlStreet (id text, name text, type text, cityid text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlBuilding (id text, latlon text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlaccom (id text, numid text, buildingid text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlberth (id text, numid text)"));
        queue.push(db.query.bind(client, "CREATE TABLE nlstand (id text, numid text)"));

        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlcity','geom',4326,'POLYGON',2)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlberth','geom',4326,'POLYGON',2)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlbuilding','geom',4326,'POLYGON',2)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlaccom','geom',4326,'POINT',2)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlstand','geom',4326,'POLYGON',2)"));

        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlberth','center',4326,'POINT',2)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nlstand','center',4326,'POINT',2)"));

        async.series(queue, function (err, results) {
            if (err) throw new Error("Async Problem: " + err);
            done();
            importNUM();
        });
    });
}

//Import House Numbers
function importNUM() {
    console.log("Processing Numbers (NUM)");
    var sources = fs.readdirSync('./tmp/num/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    numProcess(sources, 0);
}

function numProcess(sources, id) {
    if (id == sources.length) {
        if (type)
            process.exit(0);
        else
            importWPL();
    } else {

        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/num/' + source, "UTF-8");
            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var numWatch = false,
                postWatch = false,
                idWatch = false,
                placeIdWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Nummeraanduiding':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        if (!placeIdWatch)
                            idWatch = true;
                        break;
                    case 'bag_LVC:huisnummer':
                        numWatch = true;
                        break;
                    case 'bag_LVC:postcode':
                        postWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdeOpenbareRuimte':
                        placeIdWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (numWatch) {
                    result.num = text;
                    numWatch = false;
                } else if (postWatch) {
                    result.postcode = text;
                    postWatch = false;
                } else if (idWatch) {
                    result.ID = text;
                    idWatch = false;
                } else if (placeIdWatch) {
                    result.placeID = text;
                    placeIdWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Nummeraanduiding') {
                    queue.push(db.query.bind(client, "INSERT INTO nlNum(num, postcode, id, placeid) VALUES ('" + result.num + "', '" + result.postcode + "', '" + result.ID + "', '" + result.placeID + "')"));
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem");
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        numProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                numProcess(sources, ++id);
            });

            xml.on('close', function() {

            });

            xml.write(input);
        });
    }
}

//Import Cities
function importWPL() {
    console.log("Processing Cities (WPL)");
    var sources = fs.readdirSync('./tmp/wpl/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });

    wplProcess(sources, 0);
}

function wplProcess(sources, id) {
    if (id == sources.length) {
        if (type)
            process.exit(0);
        else
            importOPR();
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/wpl/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};

            var idWatch = false,
                geomWatch = false,
                nameWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Woonplaats':
                        result = {};
                        result.latlon = "";
                        break;
                    case 'bag_LVC:identificatie':
                        idWatch = true;
                        break;
                    case 'gml:LinearRing':
                        geomWatch = true;
                        break;
                    case 'bag_LVC:woonplaatsNaam':
                        nameWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (geomWatch) {
                    if (text.trim() !== "") {
                        result.latlon = text;
                        geomWatch = false;
                    }
                } else if (nameWatch) {
                    result.name = text;
                    nameWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Woonplaats') {
                    var regex = new RegExp("'", "g");
                    result.name = result.name.replace(regex, " ");

                    //Setup Geometry
                    var latlon = result.latlon.trim().split(" ");

                    var linestring = latlon[0] + " " + latlon[1];
                    for (var i = 2; i < latlon.length; i=i+2) {
                        linestring = linestring + "," + latlon[i] + " " + latlon[i+1];
                    }


                    var geom = "ST_Transform(ST_MakePolygon(ST_GeomFromText('LINESTRING(" + linestring + ")', 28992)), 4326)";

                    queue.push(db.query.bind(client, "INSERT INTO nlCity(id, name, geom) VALUES ('" + result.id + "', '" + result.name + "', " + geom + ")"));
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    console.log("Writing to PSQL");
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err +' '+results.length);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        wplProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                wplProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}

//Import Streets
function importOPR() {
    console.log("Processing Streets (OPR)");
    var sources = fs.readdirSync('./tmp/opr/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    oprProcess(sources, 0);
}

function oprProcess(sources, id) {
    if (id == sources.length) {
        if (type)
            process.exit(0);
        else
            importVBO();
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/opr/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var idWatch = false,
                nameWatch = false,
                typeWatch = false,
                cityIdWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:OpenbareRuimte':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        if (!cityIdWatch)
                            idWatch = true;
                        break;
                    case 'bag_LVC:openbareRuimteNaam':
                        nameWatch = true;
                        break;
                    case 'bag_LVC:openbareRuimteType':
                        typeWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdeWoonplaats':
                        cityIdWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (nameWatch) {
                    result.name = text;
                    nameWatch = false;
                } else if (typeWatch) {
                    result.type = text;
                    typeWatch = false;
                } else if (cityIdWatch) {
                    result.cityid = text;
                    cityIdWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:OpenbareRuimte') {
                    var regex = new RegExp("'", "g");
                    result.name = result.name.replace(regex, " ");
                    queue.push(db.query.bind(client, "INSERT INTO nlStreet(id, name, type, cityid) VALUES ('" + result.id + "', '" + result.name + "', '" + result.type + "', '" + result.cityid + "')"));
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        oprProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                oprProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}

//Import Accomadation Link
function importVBO() {
    console.log("Processing Accomadations (VBO)");
    var sources = fs.readdirSync('./tmp/vbo/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    vboProcess(sources, 0);
}

function vboProcess(sources, id) {
    if (id === sources.length) {
        if (type)
            process.exit(0);
        else
            importLIG();
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/vbo/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var idWatch = false,
                geomWatch = false,
                buildingIdWatch = false,
                numIdWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Verblijfsobject':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        if (!buildingIdWatch && !numIdWatch)
                            idWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdPand':
                        buildingIdWatch = true;
                        break;
                    case 'gml:pos':
                        geomWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdeAdressen':
                        numIdWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (geomWatch) {
                    result.latlon = text;
                    geomWatch = false;
                } else if (buildingIdWatch) {
                    result.buildingid = text;
                    buildingIdWatch = false;
                } else if (numIdWatch) {
                    result.numid = text;
                    numIdWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Verblijfsobject') {

                    //Setup Geometry

                    if (result.latlon) {
                        var latlon = result.latlon.split(" ");
                        if (latlon.length > 2) {

                            var linestring = latlon[0] + "," + latlon[1];

                            var geom = "ST_Transform(ST_SetSRID(ST_MakePoint(" + linestring + "), 28992), 4326)";

                            queue.push(db.query.bind(client, "INSERT INTO nlAccom(id, geom, numid, buildingid) VALUES ('" + result.id + "', " + geom + ", '" + result.numid + "', '" + result.buildingid + "')"));
                        }
                    }
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        vboProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                vboProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}

//Import Berths
function importLIG() {
    console.log("Processing Berths (LIG)");
    var sources = fs.readdirSync('./tmp/lig/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    ligProcess(sources, 0);
}

function ligProcess(sources, id) {
    if (id === sources.length) {
        if (type)
            process.exit(0);
        else
            importSTA();
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/lig/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var idWatch = false,
                geomWatch = false,
                numIdWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Ligplaats':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        if (!numIdWatch)
                            idWatch = true;
                        break;
                    case 'gml:LinearRing':
                        geomWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdeAdressen':
                        numIdWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (geomWatch) {
                    result.latlon = text;
                    geomWatch = false;
                } else if (numIdWatch) {
                    result.numid = text;
                    numIdWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Ligplaats') {
                    //Setup Geometry
                    var latlon = result.latlon.split(" ");

                    if (latlon.length >= 6) {

                        var linestring = latlon[0] + " " + latlon[1];
                        for (var i = 3; i < latlon.length; i=i+3) {
                            linestring = linestring + "," + latlon[i] + " " + latlon[i+1];
                        }

                        console.log(linestring + "\n");

                        var geom = "ST_Transform(ST_MakePolygon(ST_GeomFromText('LINESTRING(" + linestring + ")', 28992)), 4326)";
                        var center = "ST_Centroid(" + geom + ")";

                        queue.push(db.query.bind(client, "INSERT INTO nlBerth(id, geom, numid, center) VALUES ('" + result.id + "', " + geom + ", '" + result.numid + "', " + center + ")"));
                    }
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        ligProcess(sources, ++id);
                    });
                }

            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                ligProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}

//Import Standings
function importSTA() {
    console.log("Processing Standings (STA)");
    var sources = fs.readdirSync('./tmp/sta/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    staProcess(sources, 0);
}

function staProcess(sources, id) {
    if (id === sources.length) {
        if (type)
            process.exit(0);
        else
            genPoints();
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/sta/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var idWatch = false,
                geomWatch = false,
                numIdWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Standplaats':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        if (!numIdWatch)
                            idWatch = true;
                        break;
                    case 'gml:LinearRing':
                        geomWatch = true;
                        break;
                    case 'bag_LVC:gerelateerdeAdressen':
                        numIdWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (geomWatch) {
                    result.latlon = text;
                    geomWatch = false;
                } else if (numIdWatch) {
                    result.numid = text;
                    numIdWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Standplaats') {
                    //Setup Geometry
                    var latlon = result.latlon.split(" ");

                    if (latlon.length >= 6) {

                        var linestring = latlon[0] + " " + latlon[1];
                        for (var i = 3; i < latlon.length; i=i+3) {
                            linestring = linestring + "," + latlon[i] + " " + latlon[i+1];
                        }

                        var geom = "ST_Transform(ST_MakePolygon(ST_GeomFromText('LINESTRING(" + linestring + ")', 28992)), 4326)";
                        var center = "ST_Centroid(" + geom + ")";

                        queue.push(db.query.bind(client, "INSERT INTO nlStand(id, geom, numid, center) VALUES ('" + result.id + "', " + geom + ", '" + result.numid + "', " + center + ")"));
                    }
                } else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        staProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                staProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}


//Not Needed to Generate Address/Place geometries
//To call use node import.nl-address.js PND
//The zips must be uncompressed & tables set up first!

//Import Buildings
function importPND() {
    console.log("Processing Buildings (PND)");
    var sources = fs.readdirSync('./tmp/pnd/').filter(function(value) {
        return value.indexOf('.xml') !== 0;
    });
    pndProcess(sources, 0);
}

function pndProcess(sources, id) {
    if (id == sources.length) {
        console.log("Done!");
        process.exit(0);
    } else {
        var source = sources[id];
        console.log("  " + source);

        var start = new Date() / 1000;

        pg.connect(connect, function(err, client, done) {
            if (err) throw new Error("Could not connect to PostGreSQL");

            var input = fs.readFileSync('./tmp/pnd/' + source, "UTF-8");

            input = input.replace(new RegExp('\r?\n','g'), '');

            xml = new xmlStream.Parser('UTF-8');

            var queue = [];

            var result = {};
            var idWatch = false,
                geomWatch = false;

            xml.on('startElement', function(item) {
                switch (item) {
                    case 'bag_LVC:Pand':
                        result = {};
                        break;
                    case 'bag_LVC:identificatie':
                        idWatch = true;
                        break;
                    case 'gml:LinearRing':
                        geomWatch = true;
                        break;
                }
            });

            xml.on('text', function(text) {
                if (idWatch) {
                    result.id = text;
                    idWatch = false;
                } else if (geomWatch) {
                    result.latlon = text;
                    geomWatch = false;
                }
            });

            xml.on('endElement', function(item) {
                if (item === 'bag_LVC:Pand')
                    queue.push(db.query.bind(client, "INSERT INTO nlBuilding(id, latlon) VALUES ('" + result.id + "', '" + result.latlon + "')"));
                else if (item === 'xb:BAG-Extract-Deelbestand-LVC') {
                    async.series(queue, function (err, results) {
                        if (err) throw new Error("Async Problem: " + err);
                        var elapsed = new Date() / 1000 - start;
                        console.log("    Complete: " + elapsed + "s");
                        done();
                        pndProcess(sources, ++id);
                    });
                }
            });

            xml.on('error', function(message) {
                console.log("    ERROR! " + message);
                pndProcess(sources, ++id);
            });

            xml.write(input);
        });
    }
}


function makeCSV() {
    pg.connect(connect, function(err, client, done) {
        if (err) throw new Error("Could not connect to PostGreSQL");
        var queue = [];
        queue.push(db.query.bind(client, "COPY (SELECT ST_X(geom) AS LON, ST_Y(geom) AS LAT, num AS NUMBER, name AS STREET, postcode AS POSTCODE FROM nladdress) TO '" + process.argv[3] + "' WITH DELIMITER ',' CSV HEADER"));
        async.series(queue, function (err, results) {
            if (err) throw new Error("Async Problem: " + err);
            done();
        });
    });
}


function genPoints() {
    pg.connect(connect, function(err, client, done) {
        if (err) throw new Error("Could not connect to PostGreSQL");

        var queue = [];

        queue.push(db.query.bind(client, "CREATE TABLE nladdresstmp (num text, streetid text, postcode text, id serial)"));
        queue.push(db.query.bind(client, "SELECT AddGeometryColumn ('nladdresstmp','geom',4326,'POINT',2)"));

        queue.push(db.query.bind(client, "INSERT INTO nladdresstmp(num, streetid, postcode, geom) (SELECT num.num, num.placeid, num.postcode, ST_Centroid(sta.geom) FROM nlstand AS sta, nlnum as num WHERE sta.numid = num.id)"));
        queue.push(db.query.bind(client, "INSERT INTO nladdresstmp(num, streetid, postcode, geom) (SELECT num.num, num.placeid, num.postcode, ST_Centroid(lig.geom) FROM nlberth AS lig, nlnum as num WHERE lig.numid = num.id)"));
        queue.push(db.query.bind(client, "INSERT INTO nladdresstmp(num, streetid, postcode, geom) (SELECT num.num, num.placeid, num.postcode, vbo.geom FROM nlaccom AS vbo, nlnum as num WHERE vbo.numid = num.id)"));
        queue.push(db.query.bind(client, "CREATE TABLE nladdress AS SELECT adr.num, adr.postcode, adr.id, str.name, adr.geom FROM nladdresstmp AS adr, nlstreet AS str WHERE  adr.streetid = str.id"));
        queue.push(db.query.bind(client, "DROP TABLE nladdresstmp"));

        async.series(queue, function (err, results) {
            if (err) throw new Error("Async Problem: " + err);
            done();
        });

    });
}
