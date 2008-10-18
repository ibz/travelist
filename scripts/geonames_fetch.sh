
echo "Downloading..."

wget http://download.geonames.org/export/dump/countryInfo.txt

wget http://download.geonames.org/export/dump/admin1Codes.txt

wget http://download.geonames.org/export/dump/cities1000.zip
unzip cities1000.zip

echo "Converting..."

./geonames2sql_country.sh countryInfo.txt countries.sql
./geonames2sql_administrative_division.sh admin1Codes.txt administrative_divisions.sql
./geonames2sql_place.sh cities1000.txt places.sql

