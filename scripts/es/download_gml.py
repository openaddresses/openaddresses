# coding: utf-8

import sys, os, urllib.request

with open(sys.argv[1], 'r') as f:
    urls = f.readlines()
    for url in urls:
        url = url.rstrip("\n")
        if len(url) > 0:
            filename = sys.argv[2] + url.split('/')[-1]

            url_parts = url.split('//')
            url_parts[1] = urllib.parse.quote(url_parts[1])
            url = '//'.join(url_parts)
            urllib.request.urlretrieve(url, filename)

            sys.stdout.write('.')
            sys.stdout.flush()

# fix filenames -- unsure why this is necessary but it is
for filename in os.listdir(sys.argv[2]):
    os.rename(filename, filename.strip())
