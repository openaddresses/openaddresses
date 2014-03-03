# Global Addresses

A global collection of addresses, open and free to use. Join, download and contribute. We're just getting started.

## Downloading

    # node 0.10.x
    # Install
    npm install
    # Test availability of sources
    npm test
    # Download all sources into data/
    npm start

## Contributing addresses

- [Open an issue](https://github.com/osmlab/addresses/issues?state=open) and report an address file.
- Or create a pull request to the [sources](https://github.com/osmlab/addresses/tree/master/sources) directory.

## Use as a module

    var addresses = require('addresses');
    addresses.download({
        test: false, # true to test but not download
        source: <directorypattern>, # source yaml files to download / test
        targetStream: function(address) {
            return fs.createWriteStream((new Buffer(address.data)).toString('base64'));
        } # target stream handler
    }, callback)

## Why?

[I](http://github.com/iandees) spent a lot of time tracking down [address data](https://docs.google.com/spreadsheet/ccc?key=0AsVnlPsfrhUIdEVZTzVFalFYYnlvTkc0R05wcUpsWVE&usp=drive_web) and I want to share that work with others.

## License

Code is available under BSD, the data collection (sources/) is public domain. See respective LICENSE files in project root for code and under sources/ for the data collection.
