'use strict';

// Shared scraper for counties running WTH Technology / ThinkGIS parcel
// viewers (e.g. https://gallatinil.wthgis.com/). See README.md in this
// directory for how the site works and why this approach is needed.

function z192LL(x19, y19) {
  const x = x19 / Math.pow(2, 19);
  const y = y19 / Math.pow(2, 19);
  const originX = 128.0;
  const originY = 128.0;
  const pixelsPerLon = 256.0 / 360.0;
  const pixelsPerLonRadian = 256.0 / (2 * Math.PI);
  const lon = (x - originX) / pixelsPerLon;
  const latRadians = (y - originY) / (-pixelsPerLonRadian);
  const lat = (2 * Math.atan(Math.exp(latRadians)) - Math.PI / 2) * (180 / Math.PI);
  return [lon, lat];
}

// mirrors drawPoly5() in tgis/tgisProc2.js: first pair is an absolute point,
// every pair after that is a delta from the running position
function decodeRing(polyText) {
  const parts = polyText.split(',');
  const coords = parts.slice(2); // parts[0]=color, parts[1]=width, both unused here
  const ptCount = Math.floor(coords.length / 2);
  let x = 0;
  let y = 0;
  const ring = [];
  for (let i = 0; i < ptCount; i++) {
    x += parseInt(coords[i * 2], 10);
    y += parseInt(coords[i * 2 + 1], 10);
    ring.push(z192LL(x, y));
  }
  // the site draws these as polylines, not necessarily closed rings - GDAL
  // rejects an unclosed LinearRing, so close it if the last point didn't
  // land back on the first
  if (ring.length >= 2) {
    const [firstLon, firstLat] = ring[0];
    const [lastLon, lastLat] = ring[ring.length - 1];
    if (firstLon !== lastLon || firstLat !== lastLat) ring.push(ring[0]);
  }
  return ring;
}

function decodeGeometry(xml) {
  const rings = [];
  const polyRe = /<poly>([^<]*)<\/poly>/g;
  let m;
  while ((m = polyRe.exec(xml)) !== null) {
    const ring = decodeRing(m[1]);
    if (ring.length >= 3) rings.push(ring);
  }
  if (rings.length === 0) return null;
  return rings.length === 1
    ? { type: 'Polygon', coordinates: [rings[0]] }
    : { type: 'MultiPolygon', coordinates: rings.map((r) => [r]) };
}

// The parcel record HTML isn't consistent between counties - some use
// `<th class="leftheader">Label</th><td>Value</td>`, others use
// `<td class=ftrfld>label</td><td class=ftrval>Value</td>`. This pulls
// every label/value pair out of either shape into a plain object, keyed
// by the human-readable label (e.g. "Parcel Number", "taxID"). Values that
// span multiple lines (e.g. "322 E WASHINGTON<br>HAVANA IL 62644") come
// back as a "\n"-joined string - callers decide how to split that.
function parseFields(xml) {
  const fields = {};
  const re =
    /<(?:th class="leftheader"|td class=ftrfld)>([^<]*)<\/(?:th|td)>\s*<td(?: class=ftrval)?>([\s\S]*?)<\/td>/g;
  let m;
  while ((m = re.exec(xml)) !== null) {
    const label = m[1].replace(/&nbsp;/g, ' ').trim();
    const value = m[2]
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<[^>]*>/g, '')
      .replace(/&nbsp;/g, ' ')
      .split('\n')
      .map((line) => line.trim())
      .filter((line) => line.length > 0)
      .join('\n');
    fields[label] = value;
  }
  return fields;
}

function parseFeature(xml) {
  if (/none found/i.test(xml)) return null;
  const geometry = decodeGeometry(xml);
  if (!geometry) return null;
  return { fields: parseFields(xml), geometry };
}

async function fetchFeature(host, dsid, featureId, attempt = 1) {
  const url = `${host}/tgis/getftr.aspx?D=${dsid}&F=${featureId}&Z=1`;
  try {
    const res = await fetch(url, {
      headers: {
        'user-agent': 'openaddresses-import (parcels; contact: rmartin@rmart.in)',
        referer: `${host}/`,
        accept: '*/*'
      }
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return parseFeature(await res.text());
  } catch (err) {
    if (attempt >= 3) {
      console.warn(`F=${featureId} failed after ${attempt} attempts: ${err.message}`);
      return null;
    }
    await new Promise((r) => setTimeout(r, 500 * attempt));
    return fetchFeature(host, dsid, featureId, attempt + 1);
  }
}

// Feature ids are a small sequential range per county with no published
// upper bound, so probe for it: double up from 1 until a whole window
// comes back empty, then binary-search the boundary. Windows are checked
// with a small worker pool (not one request at a time) since a window
// beyond the real data has to be fully exhausted before it can report "no
// hit" - at concurrency 1 that's up to `windowSize` sequential round-trips
// with no visible progress in between.
async function findMaxFeatureId(host, dsid) {
  const windowSize = 200;
  const concurrency = 10;

  const hasAnyHit = async (start, end) => {
    let nextId = start;
    let found = false;
    async function worker() {
      while (!found && nextId <= end) {
        const id = nextId++;
        if (await fetchFeature(host, dsid, id)) found = true;
      }
    }
    await Promise.all(Array.from({ length: concurrency }, worker));
    return found;
  };

  console.log(`probing ${host} (D=${dsid}) for its id range...`);

  let lo = 1;
  let hi = windowSize;
  while (await hasAnyHit(hi - windowSize + 1, hi)) {
    console.log(`  ids exist up to at least ${hi}, checking further...`);
    lo = hi;
    hi *= 2;
  }

  // binary search for the last id at which a forward window still has a hit
  while (hi - lo > windowSize) {
    const mid = Math.floor((lo + hi) / 2);
    if (await hasAnyHit(mid - windowSize + 1, mid)) {
      lo = mid;
    } else {
      hi = mid;
    }
    console.log(`  narrowing id range... [${lo}, ${hi}]`);
  }
  return hi;
}

async function scrapeCounty({ host, dsid, concurrency = 5, maxFeatureId }) {
  const max = maxFeatureId || (await findMaxFeatureId(host, dsid));
  console.log(`scanning F=1..${max} on ${host} (D=${dsid})`);

  const features = [];
  let nextId = 1;
  let done = 0;

  async function worker() {
    while (nextId <= max) {
      const id = nextId++;
      const feature = await fetchFeature(host, dsid, id);
      if (feature) features.push(feature);
      done++;
      if (done % 500 === 0) {
        console.log(`processed ${done}/${max}, ${features.length} parcels found`);
      }
    }
  }

  await Promise.all(Array.from({ length: concurrency }, worker));
  return features;
}

// e.g. "HAVANA IL 62644" or "OLNEY, IL" -> { city: "HAVANA", postcode: "62644" }
// (state is dropped - every county here is IL)
function parseCityStateZip(text) {
  if (!text) return {};
  const cleaned = text.replace(/,/g, ' ').replace(/\s+/g, ' ').trim();
  const m = cleaned.match(/^(.*)\s+[A-Z]{2}(?:\s+(\d{5}(?:-\d{4})?))?$/);
  if (!m) return {};
  const result = {};
  if (m[1].trim()) result.city = m[1].trim();
  if (m[2]) result.postcode = m[2];
  return result;
}

// One feature per parcel, carrying both parcel and address attributes -
// the parcels and addresses layers in the source JSON can point at the
// same uploaded file and each conform pull out what they need (this repo
// already does that in plenty of sources, e.g. sources/au/qld/logan_city.json).
//
// address is left as a single raw string (e.g. "322 E WASHINGTON") - the
// source JSON's conform should split it with prefixed_number/postfixed_street,
// same as sources/us/mi/mason.json does for a similar parcel-derived source.
// Geometry is left as the parcel polygon; use "format": "shapefile-polygon"
// equivalent (batch-machine centroids polygon address sources) in conform.
//
// city/zip come either from a second line within addressLabel itself (e.g.
// Mason/Pike's "322 E WASHINGTON<br>HAVANA IL 62644") or, if cityStateZipLabel
// is given, from that separate field (e.g. Richland's "taxPropCityStZip").
function toGeoJSON(features, { pidLabel, addressLabel, cityStateZipLabel }) {
  const out = [];
  for (const f of features) {
    const pid = f.fields[pidLabel];
    if (!pid) continue;

    const properties = { pid };

    if (addressLabel) {
      const raw = f.fields[addressLabel];
      if (raw) {
        const lines = raw.split('\n');
        const address = lines[0].trim();
        if (address) {
          properties.address = address;
          const cszText = cityStateZipLabel ? f.fields[cityStateZipLabel] : lines[1];
          const csz = parseCityStateZip(cszText);
          if (csz.city) properties.city = csz.city;
          if (csz.postcode) properties.postcode = csz.postcode;
        }
      }
    }

    out.push({ type: 'Feature', properties, geometry: f.geometry });
  }
  return { type: 'FeatureCollection', features: out };
}

async function run({ name, host, dsid, pidLabel, addressLabel, cityStateZipLabel, maxFeatureId }) {
  const os = require('os');
  const path = require('path');
  const fs = require('fs');
  const outDir = process.env.DATA_DIR || os.tmpdir();

  const features = await scrapeCounty({ host, dsid, maxFeatureId });
  const collection = toGeoJSON(features, { pidLabel, addressLabel, cityStateZipLabel });

  const outPath = path.join(outDir, `${name}.geojson`);
  fs.writeFileSync(outPath, JSON.stringify(collection));

  const withAddress = addressLabel
    ? collection.features.filter((f) => f.properties.address).length
    : 0;
  console.log(
    `wrote ${collection.features.length} parcels (${withAddress} with an address) to ${outPath}`
  );
}

module.exports = { scrapeCounty, toGeoJSON, run };
