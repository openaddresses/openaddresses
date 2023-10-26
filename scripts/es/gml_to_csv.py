import subprocess, sys, os, tempfile, shutil, re, zipfile
import xml.sax
import csv

lookup = {}

class CSVBuilder(xml.sax.ContentHandler):
    def __init__(self, directory, lookup):
        self.lookup = lookup.lookup
        self.writers = {}
        self.object = {}

        self.out_dir = directory
        if self.out_dir[-1]!='/':
            self.out_dir += '/'

        self.collecting = False
        self.collect_pos = False
        self.collect_num = False
        self.srs = None
        self.strip_hash = re.compile(r'^#')

    def startElement(self, name, attrs):
        # overall protection from collecting non-address elements
        if name == 'AD:Address':
            self.object = {}
            self.collecting = True

        # lat/lon
        if name == 'gml:pos' and self.collecting:
            self.collect_pos = True
            self.object['pos'] = ''

        # number
        if name == 'AD:designator' and self.collecting:
            self.collect_num = True
            self.object['number'] = ''

        # street name, postal code, admin boundary
        if name == 'AD:component' and ('xlink:href' in attrs):
            lookup_key = self.strip_hash.sub('', attrs['xlink:href'])

            if self.lookup['thoroughfare'].get(lookup_key) is not None:
                self.object['street'] = self.lookup['thoroughfare'].get(lookup_key)
            elif self.lookup['admin'].get(lookup_key) is not None:
                self.object['admin'] = self.lookup['admin'].get(lookup_key)
            elif self.lookup['postal'].get(lookup_key) is not None:
                self.object['postcode'] = self.lookup['postal'].get(lookup_key)

        # detect SRS, create CSV writer if necessary
        if name == 'gml:Point':
            self.srs = attrs.get('srsName', None)
            if self.srs is not None:
                self.srs = self.srs.split(':')[-1]
                if not self.srs in self.writers:
                    self.writers[self.srs] = csv.DictWriter(open(self.out_dir + 'es-%s.csv' % self.srs, 'a'), ('lon', 'lat', 'number', 'street', 'postcode', 'admin'))
                    self.writers[self.srs].writeheader()

    def characters(self, content):
        if self.collect_pos:
            self.object['pos'] += content
        if self.collect_num:
            self.object['number'] += content

    def endElement(self, name):
        if name == 'gml:pos':
            self.collect_pos = False

        if name == 'AD:designator':
            self.collect_num = False

        if name == 'AD:Address':
            self.collecting = False
            self.writers[self.srs].writerow({
                'lon': self.object.get('pos').split(' ')[0],
                'lat': self.object.get('pos').split(' ')[1],
                'number': self.object.get('number'),
                'street': self.object.get('street'),
                'postcode': self.object.get('postcode'),
                'admin': self.object.get('admin')
            })

class LookupBuilder(xml.sax.ContentHandler):
    def __init__(self):
        self.lookup = {}
        self.collect = False

    def startElement(self, name, attrs):
        if name == 'AD:ThoroughfareName':
            self.lookup['_type'] = 'thoroughfare'
        if name == 'AD:AdminUnitName':
            self.lookup['_type'] = 'admin'
        if name == 'AD:PostalDescriptor':
            self.lookup['_type'] = 'postal'

        # begin collecting text content?
        if ((name == 'GN:text') and (self.lookup['_type'] in ('thoroughfare', 'admin'))) or ((name == 'AD:postCode') and (self.lookup['_type'] == 'postal')):
            self.collect = True

        # xlink target? if so, prepare to collect data
        if name in ('AD:ThoroughfareName', 'AD:AdminUnitName', 'AD:PostalDescriptor'):
            self.lookup['_next'] = attrs.get('gml:id')
            if not self.lookup['_type'] in self.lookup:
                self.lookup[self.lookup['_type']] = {}
            self.lookup[self.lookup['_type']][self.lookup['_next']] = ''

    def endElement(self, name):
        if name in ('GN:text', 'AD:postCode'):
            self.collect = False

        if name in ('AD:ThoroughfareName', 'AD:AdminUnitName', 'AD:PostalDescriptor'):
            self.lookup['_next'] = None
            self.lookup['_type'] = None

    def characters(self, content):
        # if collecting text content, stick in appropriate spot
        if self.collect:
            self.lookup[self.lookup['_type']][self.lookup['_next']] += content

def process_zipfile(in_filename, out_dir):
    print('converting %s, placing output into %s' % (in_filename, out_dir))

    temp_dir = tempfile.mkdtemp()

    # decompress and fix character encoding
    zip_ref = zipfile.ZipFile(in_filename, 'r')
    zip_ref.extractall(temp_dir)
    zip_ref.close()

    filename = '%s/%s' % (temp_dir, in_filename.split('/')[-1].replace('.zip', '.gml'))

    # build thoroughfare/postcode lookup
    lookup = LookupBuilder()
    with open(filename, 'r', encoding='ISO-8859-1') as gml:
        parser = xml.sax.make_parser()
        parser.setContentHandler(lookup)
        parser.parse(gml)

    # generate complete CSV
    csv_builder = CSVBuilder(out_dir, lookup)
    with open(filename, 'r', encoding='ISO-8859-1') as gml:
        parser = xml.sax.make_parser()
        parser.setContentHandler(csv_builder)
        parser.parse(gml)

    shutil.rmtree(temp_dir)

def main():
    in_dir = os.path.abspath(sys.argv[1])
    out_dir = os.path.abspath(sys.argv[2])
    filename_mappings = {}

    # load dictionary of better filenames
    with open('./spain_catastre/gml_urls.txt', 'r') as gml_urls:
        urls = gml_urls.readlines()
        for url in gml_urls:
            filename_mappings[url.split('/')[-1]] = url.split('/')[-2]

    for filename in os.listdir(in_dir):
        if os.path.isfile('%s/%s' % (in_dir, filename)) and filename.split('.')[-1].lower()=='zip':
            process_zipfile('%s/%s' % (in_dir, filename), '%s/%s' % (out_dir, filename.replace('.zip', '.csv')))

if __name__ == '__main__':
    in_file = sys.argv[1]
    out_dir = sys.argv[2]
    process_zipfile(in_file, out_dir)
