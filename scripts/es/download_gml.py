import sys, os, subprocess

with open(sys.argv[1], 'r') as f:
    urls = f.readlines()
    for url in urls:
        subprocess.call(['curl', url, '-O', sys.argv[2]])

# fix filenames -- unsure why this is necessary but it is
for filename in os.listdir(sys.argv[2]):
    os.rename(filename, filename.strip())
