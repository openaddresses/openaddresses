#!/usr/bin/env node

const EMAIL = ""

if (!EMAIL) {
  console.error('Must set EMAIL')
  process.exit(1)
}

// wgs84ToMercator
function to(lon, lat) {
  const R = 6378137 // WGS84 semi-major axis (metres)
  const x = R * (lon * Math.PI / 180)
  const y = R * Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI / 180) / 2))
  return [x, y]
}

// a bbox covering QLD, split by a single latitude which we found to avoid intersecting buildings
const splitLatitude = -25.86327258099996
const top = -10
const bottom = -50
const left = 100
const right = 170

// build the two areas split by the "split latitude"
const areas = [
  [
    to(left, top),
    to(right, top),
    to(right, splitLatitude),
    to(left, splitLatitude),
    to(left, top)
  ],
  [
    to(left, bottom),
    to(left, splitLatitude),
    to(right, splitLatitude),
    to(right, bottom),
    to(left, bottom)
  ]
]

for (const area of areas) {
  // build the request
  const areaOfInterest = {
    geometryType: "esriGeometryPolygon",
    features: [{
      geometry: {
        rings: [area],
        spatialReference: { wkid: 102100, latestWkid: 3857 }
      }
    }],
    sr: { wkid: 102100, latestWkid: 3857 }
  }

  const params = new URLSearchParams({
    f: "json",
    "env:outSR": "102100",
    Layers_to_Clip: JSON.stringify(["Generated building outlines"]),
    Area_of_Interest: JSON.stringify(areaOfInterest),
    Feature_Format: "File Geodatabase - GDB - .gdb",
    Spatial_Reference: "Same As Input",
    To_Email: EMAIL,
    Prepackaged_Data_URLs: "",
    Output_Title: "Generated building outlines within area of interest",
  })

  const baseUrl = "https://spatial.information.qld.gov.au/arcgis/sharing/servers/370fdcd7a9aa42148d497d06e6accdd1/rest/services/QSC/ClipZipShip/GPServer/ClipZipShip/submitJob"
  try {
    const res = await fetch(`${baseUrl}?${params}`, {
      "headers": {
        "accept": "*/*",
        "accept-language": "en-AU,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "no-cache",
        "content-type": "application/x-www-form-urlencoded",
        "pragma": "no-cache",
        "Referer": "https://qldspatial.information.qld.gov.au/"
      },
      "body": null,
      "method": "GET"
    })
    const data = await res.json()
    console.log(data)
  } catch (err) {
    console.error(err)
  }
}
