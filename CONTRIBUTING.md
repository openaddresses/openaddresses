# Contributing to OpenAddresses

[![Build Status](https://travis-ci.org/openaddresses/openaddresses.png?branch=master)](https://travis-ci.org/openaddresses/openaddresses)

## Reporting Issues

We'd love to hear about a new address source, fixes to an old one, or improvements. 

If opening an issue with a new datasource, first check `/sources` to make sure that we don't have it already. Not sure? Open an issue, we'd rather a duplicate than miss it altogether!

If you are reporting an error, an improvement, or a suggestion, we will do our best to review your issue and either fix or add the features to our roadmap.

## Contributing Sources

Comfortable with JSON? Feel free to submit a pull request with the data instead of opening an issue. Before asking for a merge, please keep Travis CI happy by making sure you submit well-formed JSON: green is good!

### Naming Files

Although the file name is redundant (the same information is stored in JSON), using coherent file names makes it much easier for contributers to quickly evaluate whether a souce already exists. Please follow the following convention 

Coverage | Code | Example
-------- | ---- | -------
Country  | {[ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)}.json | `ca.json`
Province | {[ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)}-{2 letterstate/province code}.json | `us-il.json`
County | {[ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)}-{2 letterstate/province code}-{county}.json | `us-co-routt.json`
City | {[ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)}-{2 letterstate/province code}-city_of_{city}.json | `ca-bc-city_of_vancouver.json`

###JSON Fields

####For Us Mortals

When creating a new source, use some combination of the following objects to define the source. Please do not invent new tags without first opening an issue for discussion. Many examples of tag combinations can be found simply by browsing the `./sources` directory.

`data` A URL referencing the dataset (Required!)

`website` A URL referencing the data portal

`license` A URL or string describing the license for the dataset

`compression` A string containing the compression type (usually `zip`)

`type` A string containing the protocol (Required! One of: `http`, `ftp`, `ESRI`)

`year` An integer containing the year the data was updated

`coverage` An object containing some combination of `country`, `state`, and either `city` or `county`. Each of which contain a String. (Required!)

`note` A String containing a human readable note.

#### The Machine World

There are also several fields that are computer-generated. please refrain from adding these, our software will generate them automatically.

`cache` A URL referencing a stable source for the raw file. If writing an application, use this instead of data, it is much more stable than using `data` directly.

`fingerprint` A String containing the MD5 hash of the zipped raw data.

`processed` A String containing a link to a standardized CSV file. Processed using [`openaddresses-conform`](https://github.com/openaddresses/openaddresses-conform).

`conform` An object containing the information necessary to convert the raw data into a standardized format.

`version` A string containing a timestamp of when the raw data was last updated.

### Formatting:

A few notes on formatting:

If a field is empty please do not set it to null or an empty string. 
Omit it entirely.

No commas at the beginning of a line, only at the end.

Four spaces for indents (No tabs!)
