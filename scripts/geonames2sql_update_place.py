#!/usr/bin/python

import sys

if len(sys.argv) != 3:
    print "Requires input and output file as parameters."
    exit(1)

f1 = file(sys.argv[1], "r")
f2 = file(sys.argv[2], "w")

try:
    f2.write("BEGIN;\n")
    line = f1.readline()
    while line:
        line = line[:-1]
        parts = line.split("\t")
        code = parts[0]
        name, name_ascii, names = [n.replace("'", "''") for n in [parts[1], parts[2], parts[3]]]
        names = [n for n in [name, name_ascii] if len(n)] + [n for n in names.split(",") if len(n) > 1]
        names = ",".join(set(names))
        country_code, administrative_division_code = parts[8], parts[10]
        country_id = "(SELECT id FROM backpacked_country WHERE code = '%s')" % country_code
        administrative_division_id = "(SELECT id FROM backpacked_administrativedivision WHERE country_id = (SELECT id FROM backpacked_country WHERE code = '%s') AND code = '%s')" \
            % (country_code, administrative_division_code)
        lat, lng = parts[4], parts[5]
        coords = "GeometryFromText('POINT(%s %s)', 4326)" % (lat, lng)
        date_modified = parts[18]
        f2.write("SELECT update_place(2, %s, '%s', '%s', %s, %s, %s, '%s', '%s');\n" % (code, name, name_ascii, country_id, administrative_division_id, coords, date_modified, names))
        line = f1.readline()
    f2.write("COMMIT;\n")
finally:
    f1.close()
    f2.close()
