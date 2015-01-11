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
evaluate whether a source already exists. Please follow the following
convention

Coverage | Code | Example
-------- | ---- | -------
Country  | [ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) | `ca.json`
Province | [ISO 3166-2 alpha-2 SubRegion Code](http://en.wikipedia.org/wiki/ISO_3166-2) | `us-il.json`
County   | Standard Name (Use underscores for spaces) | `us-co-routt.json`
City     | Standard Name (Use underscores for spaces) | `ca-bc-city_of_vancouver.json`

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
`merge=["one",…,"nth"]` | | The `merge` tag will merge several fields together. This is typically something along the lines of street-name and street-type fields. The merged field will be named `auto_street`.
`split`          |     | Some databases give the number and street in one field. The `split` tag will split the number and the street. The resulting fields will be `auto_street` and `auto_number`.
`advanced_merge` |     | Can be used to merge fields more arbitrarily. See Below.
`srs`            |     | Allows one to set a custom source srs. Currently only supported by `type:shapefile`, `type:shapefile-polygon`, and `type:csv`. Should be in the format of `EPSG:####` and can be any code supported by `ogr2ogr`. Modern shapefiles typically store their project in a `.prj` file. If this file exists, this tag should be omitted.
`file`           |     | The majority of zips contain a single shapefile. Sometimes zips will contain multiple files, or the shapefile that is needed is located in a folder hierarchy in the zip. Since the program only supports determining single shapefiles not in a subfolder, file can be used to point the program to an exact file. The proper syntax would be `"file": "addresspoints/address.shp"` if the file was under a single subdirectory called `addresspoints`. Note there is no preceding forward slash.
`encoding`       |     | A character encoding from which an input file will first be converted (into utf-8). Must be [recognizable by `iconv`](https://www.gnu.org/software/libiconv/).
`csvsplit`       |     | The character to delimit input CSV’s by. Defaults to comma.
`headers`        |     | (type `'csv'` only) Some non-latin CSVs provide header lines in native script and in latin characters. If specified, this tag determines which line will be used to determine field names for other conform tags. If not specified, row 1 is assumed. Alternately, if a CSV file lacks headers, setting `headers=-1` will add them. The autogenerated fields will be named COLUMN1, COLUMN2, COLUMN3 ... COLUMN10, COLUMN11 etc.
`skiplines`      |     | (type `'csv'` only) May be used in conjunction with `headers` (see above).  For example, if `headers` is 1 but a second header line exists and must be skipped.

##### Attribute Tags

If using a text processing tag above, the results can usually be found in the
generated `auto_number` or `auto_street` fields unless otherwise noted.
Field names are case insensitive, but contributers are encouraged to try to match the case.

 Tag | Required? | Note
---------- | --- | ----
`lon`      | Yes | The longitude field. Due to the way the conversion scripts work this is currently always going to be `x` unless using a `csv`.
`lat`      | Yes | The latitude field. Due to the way the conversion script work this is currently always going to be `y` unless using a `csv`.
`number`   | Yes | The name of the number field. This will either be the name of the field or `auto_number` if the split tool was used.
`street`   | Yes | The name of the street field. This will either be the name of the field or `auto_street` if the split or merge tools were used.
`accuracy` |     | The accuracy of the data source. See table below. Should never be 0, defaults to 5. If this is not set, address duplicates of higher accuracy will replace the addresses from this source when they are conflated.
`city`     |     | Name of the City or Municipality in which the address falls
`postcode` |     | Postcode or zip-code field in which the address falls
`district` |     | District/County/Sub-Region in which the address falls
`region`   |     | State/Region/Province in which the address falls
`addrtype` |     | Type of address. `industrial`, `residential`, etc.
`notes`    |     | Legal description of address or notes about the property.

###### Accuracy

| ID    | Type           |
| :---: | -------------- |
|   0   | User Corrected |
|   1   | Rooftop        |
|   2   | On Parcel      |
|   3   | Driveway       |
|   4   | Interpolation  |
|   5   | Unknown        |


###### Advanced Merge

This is sometimes necessary for the street number equivalent in Asian addressing
systems. The following example will add fields to the output CSV named
`custom_number` and `auto_street` that contained merged contents of the forms
`STREET_A-STREET_B-STREET_C` and `ROAD_A ROAD_B`, respectively:

```JSON
"conform": {
    "advanced_merge": {
        "custom_number": {
            "separator": "-",
            "fields": ["STREET_A", "STREET_B", "STREET_C"]
        },
        "auto_street": {
            "separator": " ",
            "fields": ["ROAD_A", "ROAD_B"]
        }
    }
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
   See [Alameda County](sources/us-ca-alameda_county.json)
   and [Virginia](sources/us-va.json) for examples.
2. **ISO 3166** with `alpha2` containing alphanumeric two-letter
   [ISO-3166-1 country code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
   or [ISO-3166-2 subdivision code](http://en.wikipedia.org/wiki/ISO_3166-2).
   See [New Zealand](sources/nz.json), [Victoria, Australia](sources/au-victoria.json),
   or [Dolnośląskie, Poland](sources/pl-dolnoslaskie.json) for examples.
3. **geometry** with _Polygon_ or _MultiPolygon_ type unprojected
   [GeoJSON geometry object](http://geojson.org/geojson-spec.html#geometry-objects).

#### Optional Tags

Although these tags are optional, their inclusion is very much appreciated.
Additional metadata helps future proof the project!

 Tag          | Note
------------- | ----
`website`     | A URL referencing the data portal
`license`     | A URL or string describing the license for the dataset
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
    "license": "http://geonb.snb.ca/downloads/documents/geonb_license_e.pdf",
    "type": "http",
    "compression": "zip",
    "conform": {
        "lon": "x",
        "lat": "y",
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
