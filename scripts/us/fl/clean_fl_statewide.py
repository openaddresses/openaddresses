import argparse
import csv
import os
import zipfile

fl_min_lon = -87.63489605
fl_min_lat = 24.39630799
fl_max_lon = -79.97430602
fl_max_lat = 31.00096799

def build_statewide_file(input_zipfile, out_filename):
    headers_written = False
    out = open(out_filename, 'w')
    writer = csv.writer(out)
    zip_archive = zipfile.ZipFile(input_zipfile)
    for f in zip_archive.infolist():
        filename = f.filename
        if 'STATEWIDE' in filename:
            continue
        local_filename = zip_archive.extract(filename)
        reader = csv.reader(open(local_filename))
        headers = next(reader)
        if not headers_written:
            writer.writerow(headers)
            headers_written = True
        lat_index = headers.index('LAT')
        lon_index = headers.index('LONG')
        for row in reader:
            lat = row[lat_index].strip()
            lon = row[lon_index].strip()
            valid_latlon = lat and lon
            if not valid_latlon:
                continue
            lat_float = float(lat)
            valid_latlon = valid_latlon and lat_float >= fl_min_lat and lat_float <= fl_max_lat
            lon_float = float(lon)
            valid_latlon = valid_latlon and lon_float >= fl_min_lon and lon_float <= fl_max_lon

            valid_latlon = valid_latlon and not (lat_float == int(lat_float) and lon_float == int(lon_float))
            if not valid_latlon:
                row[lat_index] = ''
                row[lon_index] = ''
            writer.writerow(row)
        os.unlink(filename)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('input_filename')
    parser.add_argument('output_filename')

    args = parser.parse_args()
    build_statewide_file(args.input_filename, args.output_filename)
