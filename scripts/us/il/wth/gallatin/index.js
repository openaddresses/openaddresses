'use strict';

require('../lib').run({
  name: 'gallatin',
  host: 'https://gallatinil.wthgis.com',
  dsid: 10435,
  pidLabel: 'Parcel Number'
  // no addressLabel: Site Address is empty for every parcel in this county
});
