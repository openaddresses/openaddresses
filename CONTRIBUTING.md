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

Confused? Not sure where your source fits in? Open an [issue](https://github.com/openaddresses/openaddresses/issues/new), we'd rather a duplicate than miss it altogether!

### Errors & Current Sources

If you are reporting an error, an improvement, or a suggestion, create a github issue [here](https://github.com/mapbox/mapbox-places/issues/new)
We will do our best to review your issue and either fix or add the feature(s) to our roadmap.

## Contributing Sources

Comfortable with JSON? Feel free to submit a pull request with the data instead of opening an issue. Before asking for a merge, please keep Travis CI happy by making sure you submit well-formed JSON: green is good!

For a first time contributer, getting the JSON right can be a bit of a challenge, check out other sources in `./sources/` to get an idea of what we are looking for.
Still confused? Open an issue, we'll be happy to help you out!

### Naming Files

Although the file name is redundant (the same information is stored in JSON), using coherent file names makes it much easier for contributers to quickly evaluate whether a source already exists. Please follow the following convention

Coverage | Code | Example
-------- | ---- | -------
Country  | [ISO 3166-1 alpha-2 Country Code](http://en.wikipedia.org/wiki/ISO_3166-1_alpha-2) | `ca.json`
Province | [ISO 3166-2 alpha-2 SubRegion Code](http://en.wikipedia.org/wiki/ISO_3166-2) | `us-il.json`
County | Standard Name (Use underscores for spaces) | `us-co-routt.json`
City | Standard Name (Use underscores for spaces) | `ca-bc-city_of_vancouver.json`

###JSON Fields

Sources use a standard set of attributes to allow for machine processing of each source. Use these tags where applicable. Check out other sources in the `./source/` directory for examples

#### Core Fields

Required fields are enforced by Travis CI (Our testing platform). This represents
the minimum data required to process a source. If you are not able to provide the required fields,
file a ticket instead of a pull request as the data may not be suitable for inclusion.

Tag | Note |
| --- | --- |
`data` **required** | A URL referencing the dataset. This should point to the raw data and not a web portal.
`type` **required** | A string containing the protocol (One of: `http`, `ftp`, `ESRI`)
`coverage` **required** | An object containing some combination of `country`, `state`, and either `city` or `county`. Each of which contain a String.
`compression` | Optional string containing the compression type (usually `zip`). Omit if source is not compressed.

#### Conform

Although a conform Object is not mandatory to add a source, in order for the source to be added into the end address file,
it needs a conform Object. This JSON Object tells the processing software how to handle the format as well as mapping fields to a standard set.

##### Processing Fields

Tag | Note |
--- | ---
`conform` **required** | Parent object
`type` **required** | The type properties stores the format. It can currently be either `shapefile`, `shapefile-polygon`, `csv` or `geojson` **required**
`csvsplit` | The character to delimit CSVs by. Defaults to comma.
`merge=["one", "two", ..., "nth"]` | The merge tag will merge several columns together. This is typically soemthing along the lines of street-name and street-type columns. The merged column will be named auto_street
`advanced_merge` | Can be used to merge fields more arbitrarily. See Below.
`split` | Some databases give the number and street in one column. The split tag will split the number and the street. The resulting columns will be `auto_street` and `auto_number`.
`srs` | Allows one to set a custom source srs. Currently only supported by `type:shapefile` and `type:shapefile-polygon`. Should be in the format of `EPSG:####` and can be any code supported by `ogr2ogr`. Modern shapefiles typically store their project in a `.prj` file. If this file exists, this tag should be omitted.
`file` | The majority of zips contain a single shapefile. Sometimes zips will contain multiple files, or the shapefile that is needed is located in a folder hierarchy in the zip. Since the program only supports determining single shapefiles not in a subfolder, file can be used to point the program to an exact file. The proper syntax would be `"file": "addresspoints/address.shp"` if the file was under a single subdirectory called `addresspoints`. Note there is no preceding forward slash.
`encoding` | a character encoding from which an input file will first be converted (into utf-8). Must be recognizable by iconv.
`headers` | (`conform.type==='csv'` only) some non-latin CSVs provide header lines in native script and in latin characters. If specified, this field determines which line will be used to determine column names for other conform fields. If not specified, row 1 is assumed. Alternately, if a CSV file lacks headers, setting `headers=-1` will add them. The autogenerated columns will be named COLUMN1, COLUMN2, COLUMN3 ... COLUMN10, COLUMN11 etc.
`skiplines` | (`conform.type==='csv'` only) may be used in conjunction with `headers` (see above).  For example, if `headers` is 1 but a second header line exists and must be skipped.

##### Attribute Fields

If using a text processing function above, the output field is usually `auto_number` or `auto_street` unless otherwise noted.

Tag | Note |
--- | ---
`lon` **required** | The longitude column. Due to the way the conversion scripts work this is currently always going to be `x` unless using a `csv`.
`lat` **required** | The latitude column. Due to the way the conversion script work this is currently always going to be `y` unless using a `csv`.
`number` **required** | The name of the number columm. This will either be the name of the column or `auto_number` if the split tool was used.
`street` **required** | The name of the street column. This will either be the name of the column or `auto_street` if the split or merge tools were used.
`city` | Name of the City or Municipality in which the address falls
`postcode` | Postcode or zip-code field in which the address falls
`district` | District/County/Sub-Region in which the address falls
`region` | State/Region/Province in which the address falls
`addrtype` | Type of address. `industrial`, `residential`, etc.
`notes` | Legal description of address or notes about the property.

###### Advanced Merge
This is sometimes necessary for the street number equivalent in Asian addressing
systems. The following example will add columns to the output CSV named
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



#### Optional

Although these tags are optional, their inclusion is very much appreciated.
Additional metadata helps future proof the project!

Tag | Note |
--- | ---
`website` | A URL referencing the data portal
`license` | A URL or string describing the license for the dataset
`note` | A String containing a human readable note.
`attribution` | Where the license requires attribution, add it here. example `CC-BY United Federation of Planets`

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
        "type": "shapefile"
    }
}
```

### Formatting:

A few notes on formatting:

- If a field is empty please do not set it to null or an empty string. Omit it entirely.
- No commas at the beginning of a line, only at the end.
- Four spaces for indents (No tabs!)
- No Blank lines

Although these are read by a machine, they are maintained by us mortals. Following the formatting
guidelines keeps the rest of us sane!
