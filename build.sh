#!/bin/sh
# build.sh — regenerates the site and all data files from the TEI edition.
set -e
TEI=ten-great-novels.xml

# 1. counts per place -> query.rq + wdqs-url.txt (line 1 = auto-running link)
python3 build_wdqs.py "$TEI"

# 2. correspondents.geojson + geojsonio-url.txt (data embedded in the URL)
python3 geojson_export.py "$TEI"

# 3. bipartite network of correspondents and votes
python3 tei2graphml.py "$TEI" ten-great-novels.graphml

# 4. TEI -> index.html, with both data links handed to the stylesheet
xsltproc --stringparam wdqs-url    "$(head -1 wdqs-url.txt)" \
         --stringparam geojson-url "$(head -1 geojsonio-url.txt)" \
         -o index.html tei2html.xsl "$TEI"

echo "index.html $(wc -c < index.html) B"
