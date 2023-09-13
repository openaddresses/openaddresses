#!/usr/bin/node

const puppeteer = require('puppeteer');
const fs = require('fs');

var template = fs.readFileSync('LIST_template.json').toString();
var asgs = fs.readFileSync('ASGS_LGA_2017_TAS.csv').toString().split("\n");

var asgsCode = {};
asgs.forEach((row) => {
    var records = row.split(',');
    asgsCode[records[1]] = records[0];
});

(async() => {
    const browser = await puppeteer.launch({ executablePath: '/usr/bin/chromium' });
    const page = await browser.newPage();
    await page.goto('http://listdata.thelist.tas.gov.au/opendata/index.html');
    var municipalities = await page.evaluate('getMunicipalities()')
    municipalities = municipalities.map((municipality) => {
        return municipality[2];
    });
    municipalities.forEach((municipality) => {
        var upper = municipality.toUpperCase();
        var lower = municipality.toLowerCase();
        var asgs_code = '';

        if (municipality in asgsCode) {
            asgs_code = asgsCode[municipality];
        } else {
            console.error(`Municipality \"${municipality}\" from the LIST not found in ASGS`);
        }

        var source = template
            .replace(/{UPPER_CASE_MUNICIPALITY}/g, upper)
            .replace(/{LOWER_CASE_MUNICIPALITY}/g, lower)
            .replace(/{ASGS_CODE}/g, asgs_code)

        var filename = `../../../sources/au/tas/list_${lower}_municipality.json`;
        console.log(`${upper} -> ${filename}`);
        fs.writeFileSync(filename, source);
    });
    await browser.close();
})();
