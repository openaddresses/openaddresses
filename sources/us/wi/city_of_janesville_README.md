# City of Janesville, WI - Address Data Source

## Data Source
Esri Feature Server: https://services2.arcgis.com/i52vmcFqzIWK9plW/arcgis/rest/services/OpenDataHub/FeatureServer/1

## Field Verification

**IMPORTANT**: The field names in the conform section should be verified against the actual service.

To inspect the available fields:

1. View service metadata:
   ```
   https://services2.arcgis.com/i52vmcFqzIWK9plW/arcgis/rest/services/OpenDataHub/FeatureServer/1?f=json
   ```

2. Query a sample feature to see field values:
   ```
   https://services2.arcgis.com/i52vmcFqzIWK9plW/arcgis/rest/services/OpenDataHub/FeatureServer/1/query?where=1%3D1&outFields=*&resultRecordCount=1&f=json
   ```

The current conform section uses standard Esri field name patterns based on similar modern services:
- `number`: `ADDRNUM` - Standard field for address number
- `street`: `FULLNAME` - Standard field for complete street name (including prefix direction, street name, type, suffix direction)
- `city`: `CITY` - Standard field for city/municipality name
- `postcode`: `ZIP` - Standard field for ZIP code (may also be `ZIPCODE` in some services)

**Note**: These field names follow the NENA (National Emergency Number Association) addressing standard commonly used in modern Esri services. If the service uses a different schema, the field names may vary:
- Address number alternatives: `AddNum`, `HOUSENUMBER`, `NUMBER_`
- Street name alternatives: `STREETNAME`, `STREET`, `ROAD_NAME` (if separate components, look for `PREDIR`, `STREETNAME`, `STREETTYPE`, `POSTDIR`)
- City alternatives: `CITYNAME`, `MUNICIPALITY`, `TOWN`
- Postcode alternatives: `ZIPCODE`, `ZIP5`, `POSTCODE`

## Updating the Field Names

If the actual field names differ from those in the source file:

1. Open `sources/us/wi/city_of_janesville.json`
2. Update the field names in the `conform` section to match the actual field names
3. Run `npm test` to validate the JSON structure
4. Test with the openaddresses machine to verify data extraction works correctly

## Common Field Name Patterns

Based on other Wisconsin sources, address fields often follow these patterns:
- Address components may be split (e.g., `PreDir`, `StreetName`, `StreetType`, `PostDir`)
- Full addresses may be in a single field (requiring regex or function parsing)
- Units/apartments may be separate or combined with the main address

Adjust the conform section using appropriate functions if needed (e.g., `prefixed_number`, `postfixed_street`, etc.).
