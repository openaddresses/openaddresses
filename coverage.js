var fs = require('fs');
var _ = require('underscore');
var yaml = require('js-yaml');
var glob = require('glob');
var Step = require('step');
var path = require('path');

var cov = {};
var topo;
var mapping;
var geom;



Step(
    function loadTopoJson() {
        topo = JSON.parse(fs.readFileSync('coverage/us/counties.topojson', 'utf8'));
        mapping = JSON.parse(fs.readFileSync('coverage/us/state_mapping.json'));
        return this;
    },
    function readYaml() { 
        glob('sources/us/*', this);
    },
    function processYaml(err, files) {
        _.each(files, function (file) { 
            var doc = yaml.safeLoad(fs.readFileSync(file, 'utf8'));
            _.each(doc, function(src) {
                if(!src.city && src.county) { 
                    src.state = path.basename(file, '.yaml');
                    cov[src.state + ':' + src.county.toLowerCase()] = src;       
                }
            });
        });
        return this;
    },
    function mergeProperties() {
        _.each(topo.objects.counties.geometries, function(geom) {
    
            var state = mapping[geom.properties.STATE];
            var county = geom.properties.COUNTY.replace(' County','')
                .replace(' Municipio','')        
                .replace(' (County Equivalent)','')
                .toLowerCase();
            
            // Does coverage exist for the particular county?
            if (cov[state + ':' + county]) {
                var c = cov[state + ':' + county];
                // TODO: this should be done in a more generic way
                if (c.data) geom.properties.data = c.data;
                if (c.license) geom.properties.data = c.license;
                if (c.year) geom.properties.year = c.year;
                
                topo.objects.counties.geometries[geom] = geom;
            }
        });
               
        return this;
    },
    function writeCoverage() {
        fs.writeFileSync('site/coverage/us/county/coverage.json', JSON.stringify(topo));
    }
);
        
        
