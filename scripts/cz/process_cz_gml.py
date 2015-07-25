import __future__
import sys, re, os
import xml.sax
import xmltodict
import unicodecsv as csv

def debug(x):
    sys.stderr.write('{}\n'.format(x))

class Callbacks(object):
    def __init__(self):
        self.total = 0
        self.good = 0
        self.ulice_lookup = {}
        self.writers = {}

    def handle_ulice(self, x):
        obj = xmltodict.parse(x)
        self.ulice_lookup[obj['vf:Ulice']['uli:Kod']] = obj['vf:Ulice']['uli:Nazev']

    def handle_data(self, x):
        obj = xmltodict.parse(x)['vf:Obec']
        self.place_name = obj.get('obi:Nazev', '')

    def handle_adresnimisto(self, x):
        self.total += 1

        obj = xmltodict.parse(x)['vf:AdresniMisto']

        if not obj.get('ami:Ulice',False):
            debug('ami:Kod {} - no ulice'.format(obj['ami:Kod']))
            ulice = ''
        else:
            ulice = self.ulice_lookup.get(obj['ami:Ulice']['uli:Kod'], '')
            if ulice == '':
                debug('ami:Kod {} - ulice {} not found'.format(obj['ami:Kod'], obj['ami:Ulice']['uli:Kod']))
                if self.place_name == '':
                    return

        if not obj.get('ami:Geometrie', False):
            debug('ami:Kod {} - no geometry'.format(obj['ami:Kod']))
            return

        if not obj.get('ami:CisloDomovni', False):
            debug('ami:Kod {} - no house number'.format(obj['ami:Kod']))
            return

        point = obj['ami:Geometrie']['ami:DefinicniBod']['ami:AdresniBod']['gml:Point']
        srs = point['@srsName'].split('::')[-1]
        coords = point['gml:pos'].split(' ')
        postcode = obj.get('ami:Psc','')
        number = obj['ami:CisloDomovni']

        if len(coords) != 2:
            debug('ami:Kod {} - bad coordinates {}'.format(obj['ami:Kod'], coords))
            return

        if not srs in self.writers:
            filename = 'cz-{}.csv'.format(srs)
            previously_existing_file = os.path.exists(filename)
            self.writers[srs] = csv.writer(open(filename, 'a'))
            if not previously_existing_file:
                self.writers[srs].writerow(['LON', 'LAT', 'NUMBER', 'STREET', 'CITY', 'POSTCODE'])

        self.writers[srs].writerow([coords[0], coords[1], number, ulice, self.place_name, postcode])
        self.good += 1

class XMLHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.stack = []
        self.watch = {}

    def register(self, name, callback):
        self.watch[name] = {
            'callback': callback,
            'content': '',
            'collecting': False
        }

    def startElement(self, name, attrs):

        self.stack.append(name)

        for w in self.watch:
            if '/'.join(self.stack) == w:
                self.watch[w]['collecting'] = True
                self.watch[w]['content'] = ''

        for w in self.watch:
            if self.watch[w]['collecting']:
                self.watch[w]['content'] += '<{}{}>'.format(name, ''.join(map(lambda x: ' {}="{}"'.format(x[0], x[1]), attrs.items())))

    def endElement(self, name):
        for i in xrange((len(self.stack)-1), -1, -1):
            if self.stack[i] == name:
                self.stack.pop(i)
                break

        for w in self.watch:
            if self.watch[w]['collecting']:
                self.watch[w]['content'] += '</{}>'.format(name)

        for w in self.watch:
            if '/'.join(self.stack + [name]) == w:
                self.watch[w]['callback'](self.watch[w]['content'])
                self.watch[w]['collecting'] = False
                self.watch[w]['content'] = ''

    def characters(self, content):
        for w in self.watch:
            if self.watch[w]['collecting']:
                self.watch[w]['content'] += content

def process(filename):
    handlers = Callbacks()

    # parse for city name
    with open(filename) as gml:
        handler = XMLHandler()
        handler.register('vf:VymennyFormat/vf:Data/vf:Obce/vf:Obec', handlers.handle_data)
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.parse(gml)

    # parse for street names
    with open(filename) as gml:
        handler = XMLHandler()
        handler.register('vf:VymennyFormat/vf:Data/vf:Ulice/vf:Ulice', handlers.handle_ulice)
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.parse(gml)

    # parse for address data, joined to street names
    with open(filename) as gml:
        handler = XMLHandler()
        handler.register('vf:VymennyFormat/vf:Data/vf:AdresniMista/vf:AdresniMisto', handlers.handle_adresnimisto)
        parser = xml.sax.make_parser()
        parser.setContentHandler(handler)
        parser.parse(gml)

    return {'good': handlers.good, 'total': handlers.total}

def main():
    result = process(sys.argv[1])
    result['pct'] = 100 * float(result['good']) / float(result['total'])
    print('{} - processed {} records, {} valid addresses found ({:.1f}%)'.format(sys.argv[1], result['total'], result['good'], result['pct']))

if __name__ == '__main__':
    main()
