# Contributing to OpenAddresses

[![Build Status](https://travis-ci.org/openaddresses/openaddresses.png?branch=master)](https://travis-ci.org/openaddresses/openaddresses)

## Reporting Sources & Issues

We'd love to hear about a new address source, fixes to an old one, or make improvements.

### New Sources

Have a potential source? Fantastic! Follow these steps to help us get it into the project as fast as possible!

- Check `./sources/` to make sure we don't have it already. Sources that overlap are ok as long as they are coming from different providers.
- Check the [wiki](https://github.com/openaddresses/openaddresses/wiki) to make sure it isn't listed there

Still a new source? Awesome!
- If the source is raster data (images/webmap/not downloadable) please add it to the [Raster Wiki](https://github.com/openaddresses/openaddresses/wiki/Raster-Data-Sources)
- If the source costs money, please add it to the [Commercial Wiki](https://github.com/openaddresses/openaddresses/wiki/Commercial-sources)
- If the source is parcel data, please add it to the [Parcel Wiki](https://github.com/openaddresses/openaddresses/wiki/Parcel-Sources)
- If you have an awesome link/contact but no data, add it to the [Outreach Wiki](https://github.com/openaddresses/openaddresses/wiki/Potential-Outreach)
- Finally if you have raw data, open a [issue](https://github.com/openaddresses/openaddresses/issues/new) and we'll add it for you or [add it yourself](https://github.com/openaddresses/openaddresses/blob/master/CONTRIBUTING.md)

Confused? Not sure where your source fits in?
[Open an issue](https://github.com/openaddresses/openaddresses/issues/new),
we’d rather a duplicate than miss it altogether!

### Errors & Current Sources

If you are reporting an error, an improvement, or a suggestion,
[create a github issue here](https://github.com/openaddresses/openaddresses/issues/new)
We will do our best to review your issue and either fix or add the feature(s) to our plan.

## Contributing Sources

Comfortable with JSON? Feel free to submit a pull request with the data instead of opening an issue. Before asking for a merge, please keep Travis CI happy by making sure you submit well-formed JSON: green is good!

For a first time contributer, getting the JSON right can be a bit of a challenge,
check out other sources in `./sources/` to get an idea of what we are looking for.
Still confused? [Open an issue](https://github.com/openaddresses/openaddresses/issues/new),
we’ll be happy to help you out!

### Naming Files

Although the file name is redundant (the same information is stored in JSON),
using coherent file names makes it much easier for contributers to quickly
evaluate whether a source already exists. Please use the following
conventions.

`/sources/{County}/{Region}/{Source}`

#### Directories

Coverage | Code |
-------- | ---- |
Country  | [ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
Province | [ISO 3166-2 alpha-2 SubRegion Code](http://en.wikipedia.org/wiki/ISO_3166-2)

#### Source

Coverage | Example |
-------- | ------- |
State    | us/md/statewide.json |
County   | us/md/montgomery.json |
City     | us/md/city_of_baltimore.json |

### JSON Tags

Sources use a standard set of attributes to allow for machine processing of
each source. Use these tags where applicable. Check out other sources in the
`./sources/` directory for examples

#### Core Tags

Our testing platform, Travis CI, enforces required tags. These represent the
minimum data required to process a source. If you are not able to provide the required
tags, [file an issue](https://github.com/openaddresses/openaddresses/issues/new)
instead of a pull request. We’ll determine if the data is suitable for inclusion.

 Tag          | Required? | Note
------------- | --------- | ----
`data`        | Yes | A URL referencing the dataset. This should point to the raw data and not a web portal.
`type`        | Yes | A string containing the protocol (One of: `http`, `ftp`, `ESRI`)
`coverage`    | Yes | An object containing some combination of `country`, `state`, and either `city` or `county`. Each of which contain a String. [See below for more details](#coverage-object)
`conform`     |     | Optional Object used to find address information in a source. [See below for more details](#conform-object).
`compression` |     | Optional string containing the compression type (usually `zip`). Omit if source is not compressed.

#### Conform Object

Although a conform Object is not a mandatory part of a source, it must be
present for the source to be added into the end address file. This JSON
Object tells the processing software how to handle the format as well as
mapping fields to a standard set.

Conform contains tags for preparing data and tags for converting it.
They are called [Processing Tags](#processing-tags) and [Attribute Tags](#attribute-tags).

##### Processing Tags

 Tag       | Required? | Note
---------------- | --- | ----
`type`           | Yes | The type properties stores the format. It can currently be one of `shapefile`, `shapefile-polygon`, `csv`, `geojson`, or `xml` (for GML).
`srs`            |     | Allows one to set a custom source srs. Currently only supported by `type:shapefile`, `type:shapefile-polygon`, and `type:csv`. Should be in the format of `EPSG:####` and can be any code supported by `ogr2ogr`. Modern shapefiles typically store their project in a `.prj` file. If this file exists, this tag should be omitted.
`file`           |     | The majority of zips contain a single shapefile. Sometimes zips will contain multiple files, or the shapefile that is needed is located in a folder hierarchy in the zip. Since the program only supports determining single shapefiles not in a subfolder, file can be used to point the program to an exact file. The proper syntax would be `"file": "addresspoints/address.shp"` if the file was under a single subdirectory called `addresspoints`. Note there is no preceding forward slash.
`encoding`       |     | A character encoding from which an input file will first be converted (into utf-8). Must be [recognizable by `iconv`](https://www.gnu.org/software/libiconv/).
`csvsplit`       |     | The character to delimit input CSV’s by. Defaults to comma.
`headers`        |     | (type `'csv'` only) Some non-latin CSVs provide header lines in native script and in latin characters. If specified, this tag determines which line will be used to determine field names for other conform tags. If not specified, row 1 is assumed. Alternately, if a CSV file lacks headers, setting `headers=-1` will add them. The autogenerated fields will be named COLUMN1, COLUMN2, COLUMN3 ... COLUMN10, COLUMN11 etc.
`skiplines`      |     | (type `'csv'` only) May be used in conjunction with `headers` (see above).  For example, if `headers` is 1 but a second header line exists and must be skipped.
`accuracy` |     |     | The accuracy of the data source. See table below. Should never be 0, defaults to 5. If this is not set, address duplicates of higher accuracy will replace the addresses from this source when they are conflated.
`split`          |     | **Deprecated - See Attribute functions** Some databases give the number and street in one field. The `split` tag will split the number and the street. The resulting fields will be `auto_street` and `auto_number`.

###### Accuracy

| ID    | Type           |
| :---: | -------------- |
|   0   | User Corrected |
|   1   | Rooftop        |
|   2   | On Parcel      |
|   3   | Driveway       |
|   4   | Interpolation  |
|   5   | Unknown        |

##### Attribute Tags

Attribute tags are functions or field names for mapping the source data into a given format. 

 Tag | Required? | Note
---------- | --- | ----
`number`   | Yes | The name of the number field. This will either be the name of the field or `auto_number` if the split tool was used.
`street`   | Yes | The name of the street field. This will either be the name of the field or an ordered list of fields to merge together. Use `auto_street` if the split tool was used.
`lon`      |     | The longitude column. This is required for CSV sources and should be omitted for other types.
`lat`      |     | The latitude field. This is required for CSV sources and should be omitted for other types.
`city`     |     | Name of the City or Municipality in which the address falls
`postcode` |     | Postcode or zip-code field in which the address falls
`district` |     | District/County/Sub-Region in which the address falls
`region`   |     | State/Region/Province in which the address falls
`id`       |     | Unique identifier, [such as a parcel APN](https://en.wikipedia.org/wiki/Assessor%27s_parcel_number).
`addrtype` |     | Type of address. `industrial`, `residential`, etc.
`notes`    |     | Legal description of address or notes about the property.


##### Attribute Functions

Attribute functions allow basic text manipulation to be performed on any of the given attribute tags.
This list gives a brief summary of what each function does. Examples can be found below.

Function | Note
-------- | -----
`regexp` | Allow regex find and/or replace on a given field. Useful to extract house number/street/city/region etc when the source has them in a single field
`join`   | Allow multiple fields to be joined with a given delimiter.

##### Attribute Tag Examples

###### Basic Usage

The most basic usage is simply mapping an attribute tag to a field in the source data.

_Format_
```JSON
"{Attribute Tag}": "{Field Name}"
```

_Example_
```JSON
"number": "SITUS_NUMBER",
"street": "SITUS_STREET"
```

###### Merge Field

Often times there are multiple fields that should be merged together. An array (`[]`) of field names
can be used with any attribute tag. The field names will joined with a space (` `).

_Format_
```JSON
"{Attribute Tag}": ["{Field Name}"]
```

_Example_
```JSON
"number": "SITUS_NUMBER",
"street": ["SITUS_STREET_PRE", "SITUS_STREET_NME", "SITUS_STREET_TYP", "SITUS_STREET_POST"]
```

###### regexp function

_Format_
```JSON
"{Attribute Tag}": {
    "function": "regexp",
    "field": "{Field Name}",
    "pattern": "{Regex Pattern}",
    "replace": "{Replace Pattern}"
}
```

_Example_

If no replace attribute is given, numbered capture groups are concatenated together to form the output.

```JSON
"number": {
    "function": "regexp",
    "field": "SITUS_ADDRESS",
    "pattern": "^([0-9]+)"
}
```

If a replace field is given the `pattern` is found and replaced. Numbered capture groups in the pattern can be referenced using the `${n}` syntax as below.

_Example_
```JSON
"street": {
    "function": "regexp",
    "field": "SITUS_ADDRESS",
    "pattern": "^(?:[0-9]+ )(.*)",
    "replace": "$1"
}
```

###### join function

The join function allows fields to be merged given an arbitrary delimiter. For delimiting
by spaces there is a more conscise format - see the example for `Merge Fields`

_Format_
```JSON
"{Attribute Tag}": {
    "function": "join",
    "fields": ["{Field1}", "{Field2}", "etc..." ],
    "separator": "{Separator}"
}
```

_Example_
```JSON
"number": {
    "function": "join",
    "fields": ["BLOCK_NUM", "BLOCK_GRP"],
    "separator": "-"
}
```

#### Coverage Object

Although a coverage Object is not a mandatory part of a source, its presence
provides hints about the geographic extent of the address file and is used to
render the map at [data.openaddresses.io](http://data.openaddresses.io).

This object minimally contains some combination of `country`, `state`, and
either `city` or `county`, all strings

If one of the following tags are provided, it will be used to render the source
to the map at [data.openaddresses.io](http://data.openaddresses.io):

1. **US Census** with `geoid` containing two-digit state or five-digit county
   [FIPS code](https://www.census.gov/geo/reference/codes/cou.html).
   See [Alameda County](sources/us/ca/alameda_county.json)
   and [Virginia](sources/us/va/statewide.json) for examples.
2. **ISO 3166** with `alpha2` containing alphanumeric two-letter
   [ISO-3166-1 country code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
   or [ISO-3166-2 subdivision code](http://en.wikipedia.org/wiki/ISO_3166-2).
   See [New Zealand](sources/nz/countrywide.json), [Victoria, Australia](sources/au/victoria.json),
   or [Dolnośląskie, Poland](sources/pl/dolnoslaskie.json) for examples.
3. **geometry** with _Polygon_ or _MultiPolygon_ type unprojected
   [GeoJSON geometry object](http://geojson.org/geojson-spec.html#geometry-objects).

#### Optional Tags

Although these tags are optional, their inclusion is very much appreciated.
Additional metadata helps future proof the project!

 Tag          | Note
------------- | ----
`website`     | A URL referencing the data portal
`license`     | An object with license details for the dataset. Supported properties include `url` and `text`. **Deprecated value:** a URL or string describing the license.
`note`        | A String containing a human readable note.
`attribution` | Where the license requires attribution, add it here. example `CC-BY United Federation of Planets`
`email`       | This email is used to send automated emails to the data provider if a user changes their data. Do not set unless the data provider wants to receive updates.

#### Example

```JSON
{
    "coverage": {
        "country": "ca",
        "state": "nb"
    },
    "data": "http://geonb.snb.ca/downloads/gcadb/geonb_gcadb-bdavg_shp.zip",
    "website": "http://www.snb.ca/geonb1/e/DC/catalogue-E.asp",
    "license": {"url": "http://geonb.snb.ca/downloads/documents/geonb_license_e.pdf"},
    "type": "http",
    "compression": "zip",
    "conform": {
        "number": "civic_num",
        "street": "street_nam",
        "type": "shapefile",
        "accuracy": 3
    }
}
```

### Formatting:

A few notes on formatting:

- If a tag is empty please do not set it to null or an empty string. Omit it entirely.
- No commas at the beginning of a line, only at the end.
- Four spaces for indents (No tabs!)
- No Blank lines

Although these are read by a machine, they are maintained by us mortals.
Following the formatting guidelines keeps the rest of us sane!
