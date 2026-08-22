'use strict';

require('../lib').run({
  name: 'richland',
  host: 'https://richlandil.wthgis.com',
  dsid: 823,
  // Richland's own field names differ from the other 3 counties (taxID
  // instead of "Parcel Number", etc).
  pidLabel: 'taxID',
  addressLabel: 'taxPropAddress',
  cityStateZipLabel: 'taxPropCityStZip'
});
