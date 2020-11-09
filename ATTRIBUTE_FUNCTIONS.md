# Attribute Functions

The conform section of a source contains, along with metadata, the address attributes and how to derive their values.  The address attributes are:

- `number` - the house number of an address
- `street` - the street the address is on
- `unit` - the apartment, suite, flat, etc of an address
- `city` - the city that the address is in
- `district` - one step up in the hierarchy from a city, such a county or metropolitan area
- `region` - the first level administrative divisions within a country, such as state or province
- `postcode` - the alphanumeric code used in many countries for sorting mail

Of these attributes, only `number` and `street` are required in a source.

In an ideal world, data sources would have a single field for each OpenAddresses conform attribute.  That is, there would be a single field for `number`, a single field for `street`, and so on.  Unfortunately that's rarely the case.  A common occurrence is for the house number and street name to be combined into a single field, for example "123 South Main Street".  To accommodate data sources like this, OpenAddresses source conforms support a number of functions to separate and join fields to create appropriate values.  This page details each of the available functions and ends with a section on acceptance testing for validation.

One note, however, is that functions cannot be combined at this time.  That is, a `regexp` function cannot be combined with a `prefixed_number` function to operate on a single field.

## Formatting Functions

There are two functions that are specifically designed to combine two or more fields into one.

### `join`

The `join` function combines any number of fields using a delimiter and is useful in cases where, for example, a complex house number is stored as two separate fields in the source data.  An example of this function comes from [Honolulu, HI](https://github.com/openaddresses/openaddresses/blob/master/sources/us/hi/honolulu.json):

```json
"number": {
    "function": "join",
    "fields": ["HOUSEPRFX", "HOUSENUMBR"],
    "separator": "-"
}
```

For ease of administration, large areas of the island of Honolulu, HI [are split into nine zones and each zone is split into up to nine sections](http://westhawaiitoday.com/sections/news/local-news/big-island-street-addresses.html).  These two numbers, combined with the physical house number, create the addressable house number.
Understandably, the Honolulu County GIS department stores these two fields separately but for OpenAddresses purposes, they need to be combined.  For example, the source data may look like:

```json
{
    "HOUSEPRFX": "91",
    "HOUSENUMBR": "921"
}
```

The addressable house number, when the `join` function above is applied, would be "91-921" for the address "91-921 Oaniani Street, Kapolei, HI".

#### Definition:

| parameter | value | default
| --------- | ----- | -------
| `function` | `join` |
| `field` | any field name in the data source | none
| `separator` | any string of length 0 or greater | a single space

### `format`

In some instances, the `join` function may not be enough to handle combining several fields where [two or more delimiters](https://github.com/openaddresses/openaddresses/blob/master/sources/nl/countrywide.json) or [hard-coded characters](https://github.com/openaddresses/openaddresses/blob/master/sources/cn/42/wuhan.json) are required for correct value expression.

An example of the `format` function can be in the [Netherlands](https://github.com/openaddresses/openaddresses/blob/master/sources/nl/countrywide.json):

```json
"number": {
    "function": "format",
    "fields": ["huisnummer", "huisletter", "huisnummertoevoeging"],
    "format": "$1$2-$3"
}
```

The positional numeric `$` format refers to the 1-based nth element in the `fields` array.  The `-` is a literal hyphen.

House numbers in the Netherlands are composed of a number, an optional letter, and an optional number suffix, which are concatenated using a hyphen. Some examples of this are:

- Ambachtsweg 4, Eede, NL
- Rondweg 25-k143, Bladel, NL
- Berkenring 123-m, Zundert, NL

The Netherlands GIS administration stores these three fields separately but they must be joined by the OpenAddresses source.  For example, the source data may look like:

```json
{
    "huisnummer": "25",
    "huisletter": "k",
    "huisnummertoevoeging": 143
}
```

The addressable house number, when the `format` function above is applied, would be "25-k143" for the address "Rondweg 25-k143, Bladel, NL".

One a notable behavior when using the `format` function is that if a referenced field has no value, it and the optional literal character values before it are not output.  That is, for "Ambachtsweg 4", "4" is the `huisnummer` value and both `huisletter` and `huisnummertoevoeging` have no value so the `$2-$3` part of the `format` has no effect and no literal hyphen is output.

The `format` parameter is required and has no default value.

#### Definition:

| parameter | value | default
| --------- | ----- | -------
| `function` | `format` |
| `fields` | an array of data source field names | none
| `format` | any string referencing all elements from `fields` using `$`-positional notation |

## Extraction Functions

More numerous than the formatting functions are the extraction functions.  These functions are used conditionally pull sections from larger values.

### `prefixed_number`, `postfixed_street`, and `postfixed_unit`

A number of countries, namely the United States, Canada, and others, format addresses with the house number prefixing the street name and sometimes suffixed with a unit, for example, "123 South Main Street".  The `prefixed_number`, `postfixed_street`, and `postfixed_unit` functions are for convenience to avoid the laborious and monotonous task of maintaining many copies of much more complicated `regexp` functions among a large number of sources.  Respectively, they simply return the contiguous block of numbers from the beginning and the value after those numbers.

An example usage of this is in [Asotin County, WA](https://github.com/openaddresses/openaddresses/blob/master/sources/us/wa/asotin.json):

```json
"number": {
    "function": "prefixed_number",
    "field": "address"
},
"street": {
    "function": "postfixed_street",
    "field": "address"
}
```

This example is very useful where a data source has very plain vanilla single "number+street" values, such as "123 Main Street" and "1220 Calle de Lago".  The example data source value would be:

```json
{
    "address": "123 Main Street"
}
```

`prefixed_number` and `postfixed_street` would return "123" and "Main Street" respectively.

It's quite common for a data source to contain a record that may not have a house number assigned yet (for, say, an empty lot in a new development).  If `prefixed_number` cannot find a contiguous sequence of number prefixing a value, an empty string is returned.  For example, if the data source value is "Main Street", then `prefixed_number` would return "", denoting no house number.

The implementations of `prefixed_number` and `postfixed_street` are very simple, they do not accommodate more complicated numbering schemes containing letters, or fractional or hyphenated house numbers, such as "143A Main Street", "15 1/2 South Maple Avenue", or "65-43 Austin St", respectively.

A source may not necessarily have to use both functions together in a conform but they commonly are.

It's also common for a single address field to contain a unit designator at the end, as in "123 Maple Street Apt 4A".  In this case, `postfixed_unit` should be used in combination with `postfixed_street` to extract `Apt 4A`.  Because `postfixed_street` considers the street value to be anything after the house number, it's normal to set `may_contain_units` to `true` in `postfixed_street` when using `postfixed_unit`.  

`postfixed_unit` recognizes the following words as unit designators:

* Unit
* Apartment
* Apt
* Suite
* Ste
* Building
* Bldg
* Lot
* #

Any text found after the unit designator is considered part of the unit.  The downside of this is that if a street name legitimately
contains one of these words, such as "Lindsay Lot Road", which is fortunately a fairly rare occurrence.  

#### Definition:

`prefixed_number` and `postfixed_unit` each take a single parameter named `field`:

| parameter | value | default
| --------- | ----- | -------
| `function` | `prefixed_number` / `postfixed_unit` |
| `field` | any field name in the data source | none (required)

`postfixed_street` takes two parameters: `field` (required) and `may_contain_units` (optional):

| parameter | value | default
| --------- | ----- | -------
| `function` | `prefixed_unit` |
| `field` | any field name in the data source | none (required)
| `may_contain_units` | `true` or `false` | `false`

### `remove_prefix` and `remove_postfix`

Some data sources contain, for unknown but legitimate reasons, two fields where one prefixes or postfixes another.  For example, the city of [Salem, OR](https://github.com/openaddresses/openaddresses/blob/master/sources/us/or/city_of_salem.json) has two fields, `ADDR_NUM` and `FULL_NAME`, where `ADDR_NUM` contains the house number and `FULL_NAME` contains the full street address including the house number and street name.

```json
"number": "ADDR_NUM",
"street": {
    "function": "remove_prefix",
    "field": "FULL_NAME",
    "field_to_remove": "ADDR_NUM"
}
```

In this example, if the `FULL_NAME` field value is prefixed with the `ADDR_NUM` field value, then the latter is removed and the remainder is assigned to the `street` field, otherwise the entire value found in the `FULL_NAME` field is used.

Here's an example data source record:

```json
{
    "ADDR_NUM": "2130",
    "FULL_NAME": "2130 MAPLE AV NE"
}
```

The usage of `remove_prefix` above would remove the `ADDR_NUM` from the beginning of `FULL_NAME`, resulting in:

```json
{
    "number": "2130",
    "street": "MAPLE AV NE"
}
```

All fields are required for `remove_prefix` and `remove_postfix`.

For a more complicated example, see [Grand Forks, ND](https://github.com/openaddresses/openaddresses/blob/master/sources/us/nd/grand_forks.json), where the `addrnum` field is the concatenation of house number and unit, the `fulladdr` field is the concatenation of house number and street, and the `unit` field contains only the unit number.

#### Definition:

| parameter | value | default
| --------- | ----- | -------
| `function` | `remove_prefix` / `remove_postfix` |
| `field` | any field name in the data source | none (required)
| `field_to_remove` | any field name in the data source | none (required)

### `regexp`

The `regexp` function is the immensely powerful yet arcane [sonic screwdriver](https://en.wikipedia.org/wiki/Sonic_screwdriver) for when no other extraction functions are an appropriate fit.  Their usage is found where source data is messy or several OpenAddresses attribute values are contained in one source field.

The term "regexp" refers to [regular expressions](http://www.regular-expressions.info/), patterns used for searching for sequences in larger pieces of text.  A full tutorial on regular expressions it outside the purpose of this documentation but there [are](http://www.regular-expressions.info/tutorial.html) [plenty](https://regexone.com/) [available](http://www.rexegg.com/).

The `regexp` function needs to know which field to operate on (`field`) and the codified search expression (`pattern`).  Optionally, the specific captured group to extract can be specified with `replace`; otherwise all captured groups are concatenated and returned.

An example of `regexp` usage can be found in [Yolo County, California](https://github.com/openaddresses/openaddresses/blob/master/sources/us/ca/yolo.json):

```json
"number": {
    "function": "regexp",
    "field": "Address",
    "pattern": "^([0-9]+)"
},
"street": {
    "function": "regexp",
    "field": "Address",
    "pattern": "^(?:[0-9]+ )(.*)",
    "replace": "$1"
}
```

The `pattern` for `number` matches a contiguous block of one or more numbers from the beginning of `Address` and assigns to the `number` field whereas the `pattern` for `street` matches everything after the numbers at the beginning of `Address` and assigns to the `street` field.  Here's an example data source record:

```json
{
    "Address": "617 TUMBLEWEED TRL"
}
```

The application of the `number` and `street` regular expressions would result in the following:

```json
{
    "number": "617",
    "street": "TUMBLEWEED TRL"
}
```

When using the `replace` parameter, add the positional captured groups in the desired format, with each group number prefixed with a `$`.  For example, `$1` would use the first captured group for the attribute value.

While virtually all modern regular expression flavors share identical basic behavior, there can be subtle nuances.  The code that executes the `regexp` conform implementations is written in Python so please write regular expressions [accordingly](https://docs.python.org/3/library/re.html).

#### Definition:

| parameter | type | value | default
| --------- | ---- | ----- | -------
| `function` | string | `regexp` |
| `field` | string | any field name in the data source | none (required)
| `pattern` | string | a compilable regular expression | none (required)
| `replace` | string | a string referencing 0 or more captured groups in `pattern` | none (optional)

### `get`
The `get` function is particularly useful in a situation when a single address record may contain multiple nodes having the same field name.

To make it less vague, let's consider an example of Polish addresses. Below you can see a single address record containing 4 same-named nodes `jednostkaAdministracyjna`, which indicates an administrational unit.  


```xml
    <address>
        ...
        <jednostkaAdministracyjna>Polska</jednostkaAdministracyjna>
        <jednostkaAdministracyjna>kujawsko-pomorskie</jednostkaAdministracyjna>
        <jednostkaAdministracyjna>brodnicki</jednostkaAdministracyjna>
        <jednostkaAdministracyjna>Bartniczka</jednostkaAdministracyjna>
    </address>

```

We want to get information about the district which is located in the fourth node (Bartniczka). In order to do that we can use the `get` method and leverage the `index` parameter. Since we are all programmers, we count starting from 0. So, the fourth field means `index` equals to 3. 


```json
"district": {
    "function": "get",
    "field": "jednostkaadmnistracyjna",
    "index": 3
}
```

#### Definition:

| parameter | type | value | default
| --------- | ---- | ----- | -------
| `function` | string | `get` |
| `field` | string | any field name in the data source | none (required)
| `index` | string | an index of the element in the sequence created by same-named elements | none (required)

## Compound functions

Sometimes a single conform function is not enough to correctly process a source field, but applying two or more functions would be simpler and more correct than writing a regex.

### `chain`

The `chain` function allows for combining any number of conform functions as a sequence. The most common use case is when a source field contains `number`, `street`, and `unit` e.g. "310 WOOD ST APT 3" and "APT 3" is also listed as a separate field. Without writing a regex (which can be complex if there are many unit types), it would be impossible to extract "WOOD ST" as the `street` field. However, with `chain`, it can be easily accomplished by first extracting the street name + unit with `postfixed_street` and then removing the unit field using `remove_postfix`. Here's an example of a conform which does just that:

```json
"number": {
    "function": "prefixed_number",
    "field": "Prop_Addr"
},
"street": {
    "function": "chain",
    "variable": "street_wip",
    "functions": [
        {
            "function": "postfixed_street",
            "field": "Prop_Addr"
        },
        {
            "function": "remove_postfix",
            "field": "street_wip",
            "field_to_remove": "Prop_Addr_Unit"
        }
    ]
},
"unit": "Prop_Addr_Unit"
```

The `variable` parameter in a `chain` function is a user-defined field which stores the intermediate results of the chain. In the first step in the `street` field example above, `postfixed_street` removes the house number, but the result of that computation is stored in the temporary field `street_wip` instead of an output field. In step 2, `street_wip` is referenced as the input field instead of the source field `Prop_Addr`. A `chain` function can contain any number of steps and the user-defined variable will accumulate the results of each step. The only requirement for user-specified variable names is that they should not conflict with the source fields or the standard output field names used in OpenAddresses conforms e.g. `street`, `number`, etc.

Given the following source record:

```json
{
    "Prop_Addr": "310 WOOD ST APT 3",
    "Prop_Addr_Unit": "APT 3"
}
```

Applying the above conform results in the following:

```json
{
    "number": "310",
    "street": "WOOD ST",
    "unit": "APT 3"
}
```

#### Definition:

| parameter | value | default
| --------- | ----- | -------
| `function` | `chain` |
| `variable` | a temporary field name to store intermediate results | none (required)
| ` functions` | a list of conform function definitions (which can also be `chain`) | none (required)

## Acceptance Testing

Arguably, the hardest part about defining sources correctly is making sure that the functions are configured correctly.  To address this, OpenAddresses recently adopted including acceptance tests in sources to provide a test bed that serves to provide both a set of test inputs and outputs and an historical record of what data formats the source contains.  Examples of acceptance tests are available for [Curry County, OR](https://github.com/openaddresses/openaddresses/blob/master/sources/us/or/curry.json) and [Montgomery County, TX](https://github.com/openaddresses/openaddresses/blob/master/sources/us/tx/montgomery.json).

Acceptance tests are entirely optional but are helpful in maintaining sources.  For example, some sources, like the [Czech Republic](https://github.com/openaddresses/openaddresses/blob/master/sources/cz/countrywide.json), contain highly complicated and fragile `regexp` patterns.  The acceptance tests provide a codified justification for the complexity of the patterns so future maintainers have a base level of understanding that doesn't have to be learned the hard way.  While optional, acceptance tests are recommended for all but the most trivial `regexp` patterns.

The `test` element is a child of the source root and contains the following required fields:

| property | type | description | values
| -------- | ---- | ----------- | ------
| `enabled`  | boolean | signals the machine to run the tests | `true` or `false`
| `description` | string | high-level summary of the tests | any string
| `acceptance-tests` | array | list of tests to run |

Each test in `acceptance-tests` contains the following required fields:

| property | type | description | values
| -------- | ---- | ----------- | ------
| `description` | string | summary of the test | any string
| `inputs` | object | map of source key -> value | string->string mapping
| `expected` | object | map of output attribute -> value | string->string mapping, keys are conform attribute names

The [machine](https://github.com/openaddresses/machine) runs the acceptance tests when `enabled` is set to `true`.  As it operates on all defined attributes in the source conform, all data source fields used by the source conform must be defined in `inputs`.

### Example

The following is an example for defining tests that use regular expressions to extract a number and street from an input field named `address` where the former prefixes the latter:

```json
"test": {
  "enabled": true,
  "description": "house numbers should prefix streets",
  "acceptance-tests": [
    {
      "description": "the house number consists of only digits",
      "inputs": {
        "address": "123 Main Street"
      },
      "expected": {
        "number": "123",
        "street": "Main Street"
      }
    },
    {
      "description": "the house number can be postfixed with a letter",
      "inputs": {
        "address": "123A Main Street"
      },
      "expected": {
        "number": "123A",
        "street": "Main Street"
      }
    }
  ]
}
```
