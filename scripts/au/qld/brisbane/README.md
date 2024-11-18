# au/qld/brisbane update script

The upstream source CSV includes a pipe (`|`) character within the `EASTING` and `NORTHING` fields which makes it unable to be directly processed by OpenAddresses.

This script will fetch the latest CSV file, and remove the pipe character, taking only the first coordinate. It's unclear what the pipe represents, but it could represent multiple geometry representations of the address.
