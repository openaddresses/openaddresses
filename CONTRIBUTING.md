# Contributing to OpenAddresses

## Reporting Issues

We'd love to hear about a new address source, fixes to an old one, or 
improvements. 

If opening an issue with a new datasource, first check `/sources` to 
make sure that we don't have it already. Not sure? Open an issue, we'd 
rather a duplicate than missing it altogether!

If you are reporting an error, and improvement, or a suggestion, we will 
do our best to review your issue and either fix or add the features to 
our roadmap.

## Contributing Sources

Comfortable with JSON? Feel free to submit a pull request with the data 
instead of opening an issue. 

JSON fields include:

`data` A URL referencing the dataset
`website` A URL referencing the data portal
`license` A URL or string containing the license
`compression` A string containing the compression type (usually `zip`)
`type` A string containing the protocol (`http`, `ftp`, `ESRI`)
`year` An int containing the year the data was updated

`coverage` An object containing some combination of `country`, 
`state`, `city`.

Formatting:
A few notes on formatting:

If a field is empty please do not set it to null or an empty string. 
Omit it entirely.

No commas at the beginning of a line, only at the end.

Four spaces for indents (No tabs!)
