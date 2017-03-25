import csv
import sys
import subprocess

if (len(sys.argv) < 2):
    sys.exit('Usage: python korea.py file1 [file2 ...]')

filenames = sys.argv[1:]

for filename in filenames:
    infile = open(filename)
    outfile = open('{}.out'.format(filename), 'w')
    reader = csv.reader(infile, delimiter='|')
    writer = csv.writer(outfile, delimiter='|')
    for line in reader:
        building_number = line[9]
        building_sub = line[10]
        if building_number and not all((c == '0' for c in building_sub)):
            building_number = '-'.join((building_number, building_sub))
        writer.writerow(list(line) + [building_number])
    subprocess.check_call(['mv', '{}.out'.format(filename), filename])
    infile.close()
    outfile.close()
