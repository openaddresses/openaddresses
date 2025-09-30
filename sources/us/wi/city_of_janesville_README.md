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

The current conform section uses common Esri field name patterns:
- `number`: `ADDNUM` - May also be named `ADDRNUM`, `AddNum`, `HOUSENUMBER`, etc.
- `street`: `STREETNAME` - May also be named `STREET`, `ROAD_NAME`, `StreetName`, etc.
- `city`: `CITY` - May also be named `CITYNAME`, `MUNICIPALITY`, etc.
- `postcode`: `ZIP` - May also be named `ZIPCODE`, `ZIP5`, `POSTCODE`, etc.

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
