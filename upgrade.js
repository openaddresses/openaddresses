#! /usr/bin/env node

const glob = require('glob');
const fs = require('fs');

glob.sync('sources/**/*.json').forEach(source => {
    const s = JSON.parse(fs.readFileSync(source, 'utf8'));

    const v2 = {
        coverage: s.coverage,
        layers: {
            addresses: [{
                type: s.type,
                data: s.data,
                website: s.website,
                email: s.email,
                conform: s.conform,
                compression: s.compression,
                license: s.license,
                note: s.note,
                attribution: s.attribution,
                language: s.language,
                year: s.year,
                skip: s.skip,
                test: s.test
            }],
            buildings: [ ]
        }
    }

    fs.writeFileSync(source, JSON.stringify(v2, null, 4));
});
