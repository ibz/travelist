#!/usr/bin/python

import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from backpacked import models

if len(sys.argv) != 3:
    print "Requires input and output file as parameters."
    exit(1)

countries = dict((c.code, c.id) for c in models.Country.objects.all())
administrative_divisions = dict(((a.country_id, a.code), a.id) for a in models.AdministrativeDivision.objects.all())

f1 = file(sys.argv[1], "r")
f2 = file(sys.argv[2], "w")

try:
    f2.write("BEGIN;\n")
    f2.write("CREATE TABLE __geonames_update_place(added int, updated int, unchanged int);\n")
    f2.write("INSERT INTO __geonames_update_place(added, updated, unchanged) VALUES (0, 0, 0);\n")
    f2.write("\\o /dev/null\n")
    line = f1.readline()
    while line:
        line = line[:-1]
        parts = line.split("\t")
        code = parts[0]
        name, name_ascii, names = [n.replace("'", "''") for n in [parts[1], parts[2], parts[3]]]
        names = [n for n in [name, name_ascii] if len(n)] + [n for n in names.split(",") if len(n) > 1]
        names = ",".join(set(names))
        country_id = countries[parts[8]]
        administrative_division_id = administrative_divisions.get((country_id, parts[10]), "NULL")
        lat, lng = parts[4], parts[5]
        coords = "GeometryFromText('POINT(%s %s)', 4326)" % (lat, lng)
        date_modified = parts[18]
        f2.write("SELECT update_place(2, %s, '%s', '%s', %s, %s, %s, '%s', '%s');\n" % (code, name, name_ascii, country_id, administrative_division_id, coords, date_modified, names))
        line = f1.readline()
    f2.write("\\o\n")
    f2.write("SELECT * FROM __geonames_update_place;\n")
    f2.write("DROP TABLE __geonames_update_place;\n")
    f2.write("COMMIT;\n")
finally:
    f1.close()
    f2.close()
