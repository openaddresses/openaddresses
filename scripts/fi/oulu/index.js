var fs        = require('fs')
  , http      = require('http')
  , XmlStream = require('xml-stream')
  ;


var out = fs.createWriteStream('osoitteet.txt', {'flags': 'w'});
out.write("STREET,NUMBER,LAT,LON\n")

var addresses = [];
var streets = {};

http.get('http://kartta.ouka.fi/web/siirto/osoitteet.xml').on('response', function(res) {
  res.setEncoding('utf8');
  var xml = new XmlStream(res);

  xml.on('endElement: Address', function(item) {
    addresses.push({
      number: item.AddressNumber,
      streetId: item.IdStreetName,
      x: item.xVis,
      y: item.yVis,
    });
  });

  xml.on('endElement: StreetName', function(item) {
    streets[item.IdStreetName] = item.NameLang1
  });

  xml.on('endElement: teklaXcitySearchConfiguration', function(){
    addresses.forEach(function(address){
      out.write(streets[address.streetId] + ',' + address.number + ',' + address.x + ',' + address.y + '\n');
    });
  });
});
