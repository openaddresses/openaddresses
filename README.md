# Global Addresses

A global collection of address data sources, open and free to use. Join, download and contribute. We're just getting started.

## Contributing addresses

- [Open an issue](https://github.com/osmlab/addresses/issues/new) and give information about where to find more address data. Be sure to include a link to the data and a description of the coverage area for the data.
- You can also create a pull request to the [sources](https://github.com/osmlab/addresses/tree/master/sources) directory.

## Usage

The goal for this project is simply to collect data sources, but there is some node code that checks if the sources still exist and can download the sources to your computer for further use.

### Install and download

    # node 0.10.x
    # Use NPM to install dependencies
    npm install
    # Check that address source data is still available
    npm test
    # Download all source data into data/
    npm start

### Use as a module

```javascript
var addresses = require('addresses');
addresses.download({
    test: false, # true to test but not download
    source: <directorypattern>, # source yaml files to download / test
    targetStream: function(address) {
        return fs.createWriteStream((new Buffer(address.data)).toString('base64'));
    } # target stream handler
}, callback)
```

## Why collect addresses?

[Ian](http://github.com/iandees) spent a lot of time tracking down [address data](https://docs.google.com/spreadsheet/ccc?key=0AsVnlPsfrhUIdEVZTzVFalFYYnlvTkc0R05wcUpsWVE&usp=drive_web) for the US and he wanted to share that work with others.

## License

Code is available under BSD, the data collection (sources/) is public domain. See respective LICENSE files in project root for code and under sources/ for the data collection.
