#!/bin/sh

echo "Downloading..."

wget http://download.geonames.org/export/dump/countryInfo.txt -O scripts/data/countries.txt

wget http://download.geonames.org/export/dump/admin1Codes.txt -O scripts/data/administrative_divisions.txt

wget http://download.geonames.org/export/dump/cities1000.zip -O scripts/data/places.zip
unzip scripts/data/places.zip -d scripts/data
rm scripts/data/places.zip
mv scripts/data/cities1000.txt scripts/data/places.txt

echo "Converting..."

# for initial data

scripts/geonames2sql_country.sh scripts/data/countries.txt scripts/data/countries.sql
scripts/geonames2sql_administrative_division.sh scripts/data/administrative_divisions.txt scripts/data/administrative_divisions.sql
scripts/geonames2sql_place.sh scripts/data/places.txt scripts/data/places.sql

# for UPDATE

scripts/geonames2sql_update_place.py scripts/data/places.txt scripts/data/update_places.sql
