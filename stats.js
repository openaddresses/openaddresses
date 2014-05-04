#!/usr/bin/env node

//NPM Dependancies
var argv = require('minimist')(process.argv.slice(2)),
    fs = require('fs');

//Command Line Args
var command = argv._[0];

if (!command) {
    console.log('usage: index.js <command>\n');
    console.log('<command>      Description ');
    console.log('  processed    List # of Processed files');
    console.log('  unprocessed  List # of unprocessed files');
    console.log('  cached       List # of cached files');
    console.log('  uncached     List # of uncached files');
    process.exit(0);
}

//Setup list of sources
var sources = fs.readdirSync(sourceDir);

//Only retain *.json
for (var i = 0; i < sources.length; i++) {
    if (sources[i].indexOf('.json') == -1) {
        sources.splice(i, 1);
        i--;
    }
}