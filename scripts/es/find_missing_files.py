# finds files that were not successfully converted; when I ran the code,
# this revealed 14, all of which had misformed URLs. I corrected them
# manually and re-ran the import

import os

GML_PATH = './spain_catastre/gml'

if __name__ == '__main__':
    for f in os.listdir(GML_PATH):
        parts = f.split('.')
        if parts[-1] == 'zip':
            csv_filename = ('.'.join(parts[:-1])) + '.csv'
            if not os.path.exists('./build/' + csv_filename):
                print('%s/%s' % (GML_PATH, f))
