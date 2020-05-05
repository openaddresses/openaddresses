import sys
import os
import xml.sax
from pyproj import Transformer

input_file = sys.argv[1]
output_file = input_file.replace(".xml", "") + ".csv"

output = open(output_file, "w")
tags = ["bt:lokalnyId", "prg-ad:kodPocztowy", "prg-ad:miejscowosc", "prg-ad:ulica", "prg-ad:numerPorzadkowy", "gml:pos"]

transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326")

class AddressHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.CurrentData = ""
        self.gugikId = ""
        self.postcode = ""
        self.city = ""
        self.street = ""
        self.houseNumber = ""
        self.geo = ""
        self.read = False

    def clear(self):
        self.gugikId = ""
        self.postcode = ""
        self.city = ""
        self.street = ""
        self.houseNumber = ""
        self.geo = ""

   # Call when an element starts
    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag in tags:
            self.read = True

   # Call when an elements ends
    def endElement(self, tag):
        if tag in tags:
            self.read = False

        if tag == "prg-ad:PRG_PunktAdresowy":
            lat, lon = self.geo.split(' ')
            x2, y2 = transformer.transform(lat, lon)
            converted_geo = '%s,%s' % (x2, y2)

            output.write("%s,%s,%s,%s,%s,%s\n" % (self.gugikId, self.postcode, self.city, self.street, self.houseNumber, converted_geo))
            self.gugikId = ""
            self.postcode = ""
            self.city = ""
            self.street = ""
            self.houseNumber = ""
            self.geo = ""

    # Call when a character is read
    def characters(self, content):
        if self.read:
            if self.CurrentData == "bt:lokalnyId":
                self.gugikId += content
            if self.CurrentData == "prg-ad:kodPocztowy":
                self.postcode += content
            elif self.CurrentData == "prg-ad:miejscowosc":
                self.city += content
            elif self.CurrentData == "prg-ad:ulica":
                self.street += content
            elif self.CurrentData == "prg-ad:numerPorzadkowy":
                self.houseNumber += content
            elif self.CurrentData == "gml:pos":
                self.geo += content


############
parser = xml.sax.make_parser()
parser.setFeature(xml.sax.handler.feature_namespaces, 0)
Handler = AddressHandler()
parser.setContentHandler(Handler)
parser.parse(input_file)

sys.stderr.write("Finished!\n")
output.close()