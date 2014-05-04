#!/usr/bin/env node

//NPM Dependancies
var fs = require('fs');

//Setup list of sources
var sources = fs.readdirSync(sourceDir);

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



sources.forEach(function(source){
    fs.readFile(file, 'utf8', function (err, data) {
        if (err) {
            return new Error("Can't Access: '" + source + "'");
        }
        
        try {
            var data = JSON.parse(data);
        } catch (err) {
            return new Error("Invalid JSON: '" + source + "'");    
        }
        
        if (data.processed)
            processed.push(source);
        else
            unprocessed.push(source);
        
        if (data.cached)
            cached.push(source);
        else
            uncached.push(source);
        
        if (data.skip)
            skip.push(source);
    });
});

console.log("OpenAddresses Stats Report\n");
console.log("Total Sources: " + total);
console.log("-------------------");
console.log("Cached: " + cached.length);
console.log("Uncached: " + total - cached.length);
console.log("Processed: " + processed.length);
console.log("Unprocessed: " + total - processed.length);