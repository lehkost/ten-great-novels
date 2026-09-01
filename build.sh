#!/bin/sh
# build.sh: regenerates the site and all data files from the TEI edition.
set -e
TEI=data/ten-great-novels.xml

# 1. counts per place -> query.rq + wdqs-url.txt (line 1 = auto-running link)
python3 scripts/build_wdqs.py "$TEI"

# 2. correspondents.geojson + geojsonio-url.txt (data embedded in the URL)
python3 scripts/geojson_export.py "$TEI"

# 3. bipartite network of correspondents and votes
python3 scripts/tei2graphml.py "$TEI" ten-great-novels.graphml

# 4. TEI -> index.html, with both data links handed to the stylesheet
xsltproc --stringparam wdqs-url    "$(head -1 wdqs-url.txt)" \
         --stringparam geojson-url "$(head -1 geojsonio-url.txt)" \
         -o index.html xslt/tei2html.xsl "$TEI"

# 5. schema.org metadata as a standalone file, lifted out of the page
python3 scripts/extract_jsonld.py index.html schema.jsonld

echo "index.html $(wc -c < index.html) B"
