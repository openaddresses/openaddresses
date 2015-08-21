var glob = require('glob'),
    fs = require('fs'),
    request = require('request');

    var manifest = glob.sync('sources/**/*.json');

manifest.forEach(function(source) {
    s = require(__dirname + '/../' + source);

    // ===== Transform Here =====

    if (s.type !== "ESRI") return;
    if (!s.conform) return;

    s.conform.type = 'geojson';
    delete s.conform.lat;
    delete s.conform.lon;

    // ===== End Transform ======

    fs.writeFileSync(__dirname + '/../' + source, JSON.stringify(s, null, 4));
});
