var glob = require('glob'),
    fs = require('fs'),
    request = require('request');

    var manifest = glob.sync('sources/**/*.json');

manifest.forEach(function(source) {
    s = require(__dirname + '/../' + source);

    // ===== Transform Here =====

    if (s.coverage.country !== 'jp') return;
    delete s.conform.advanced_merge;
    s.conform.number = {
        "function": "join",
        "fields": ["\u8857\u533a\u7b26\u53f7\u30fb\u5730\u756a","\u5ea7\u6a19\u7cfb\u756a\u53f7"],
        "separator": "-"
    }

    // ===== End Transform ======

    fs.writeFileSync(__dirname + '/../' + source, JSON.stringify(s, null, 4));
});
