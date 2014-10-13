# OpenAddresses

A global collection of address data sources, open and free to use. Join, download and contribute. We're just getting started.

This repository is a collection of references to address data sources.

- See [openaddresses-download](https://github.com/openaddresses/openaddresses-download)
for a tool to download this data.
- See [openaddresses.io](http://openaddresses.io/) for a data download.

## Contributing addresses

- [Open an issue](https://github.com/openaddresses/openaddresses/issues/new) and give information about where to find more address data. Be sure to include a link to the data and a description of the coverage area for the data.
- You can also create a pull request to the [sources](https://github.com/openaddresses/openaddresses/tree/master/sources) directory.

## Why collect addresses?

Street address data is essential infrastructure. Street names, house numbers and zip codes, when combined with geographic coordinates, are the hub that connects digital to physical places. Precisely because of their connecting role, free and open addresses are rocket fuel for civic and commercial innovation.

## License

Code is available under BSD, the data collection (sources/) is public domain. See respective LICENSE files in project root for code and under sources/ for the data collection.

## Status
[![Build Status](https://travis-ci.org/openaddresses/openaddresses.png?branch=master)](https://travis-ci.org/openaddresses/openaddresses)
[![Build Status](https://david-dm.org/openaddresses/openaddresses.png)](https://david-dm.org/openaddresses/openaddresses)

The Travis=CI build status should be used as a guide for developers adding sources to the project. Failure of the build means that one of the `data` URLs is unreachable. Since the `data` URLs are referencing 3rd party services, we cannot guarantee that the `data` URLs will be functioning at a particular time. That said, we highly recommend using the `cache` URLs. `cache` files are identical to the `data` files except that they are hosted by us on s3. These files will be updated as more data becomes available and are much more stable. `cache` URLs can be used in conjunction with `version` and `fingerprint`. Both of which allow one to determine if we have pushed updates to the cache.
