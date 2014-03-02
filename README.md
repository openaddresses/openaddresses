# osmlab addresses

A repository of tools to retrieve and build an open database of addresses for the world.

We are just starting: https://github.com/osmlab/addresses/issues?state=open

## Installation

    # node 0.10.x
    # Install
    npm install

## Use (command line)

    # Test availability of sources
    npm test
    # Download all sources into data/ (needs work)
    npm start

## Use (module)

    var addresses = require('addresses');
    addresses.download({
        test: false, # true for testing availability, false for downloading
        source: <directorypattern>, # source yaml files to download / test
        targetStream: function(address) {
            return fs.createWriteStream((new Buffer(address.data)).toString('base64'));
        } # target stream handler
    }, callback)

## Why?

[I](http://github.com/iandees) spent a lot of time tracking down [address data](https://docs.google.com/spreadsheet/ccc?key=0AsVnlPsfrhUIdEVZTzVFalFYYnlvTkc0R05wcUpsWVE&usp=drive_web) and I want to share that work with others.

## License

Code is available under BSD, the data collection (sources/) is public domain.
