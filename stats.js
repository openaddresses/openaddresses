#!/usr/bin/env node

//NPM Dependancies
var fs = require('fs'),
    _ = require('underscore');

//Setup list of sources
var sources = fs.readdirSync("./sources/");

//Only retain *.json
for (var i = 0; i < sources.length; i++) {
    if (sources[i].indexOf('.json') == -1) {
        sources.splice(i, 1);
        i--;
    }
}

var total = sources.length;
var processed = [],
    unprocessed = [],
    cached = [],
    uncached = [],
    skip = [];



sources.forEach( function(source) {
    var input;
    
    try {
        input = fs.readFileSync("./sources/" + source)
    } catch (err) {
        return new Error("Can't Access: '" + source + "'");
    }

    try {
        var data = JSON.parse(input);
    } catch (err) {
        return new Error("Invalid JSON: '" + source + "'");    
    }

    if (!data.processed)
        unprocessed.push(source);
    else
        processed.push(source);

    if (!data.cache)
        uncached.push(source);
    else
        cached.push(source);

    if (data.skip)
        skip.push(source);
});

console.log("OpenAddresses Stats Report\n");
console.log("Total Sources: " + total);
console.log("--------------------------------------------");
console.log("Cached: " + cached.length);
console.log("Uncached: " + uncached.length);
console.log("Processed: " + processed.length);
console.log("Unprocessed: " + unprocessed.length);
console.log("--------------------------------------------");
console.log("List of Uncached:");
uncached.forEach(function(source) {
    console.log("  " + source);
});
console.log("--------------------------------------------");
console.log("List of Unprocessed But Cached");

_.intersection(unprocessed, cached).forEach(function(source) {
    console.log("  " + source);
});