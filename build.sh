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

# 3b. one image per author, per novel and per correspondent -> images-<group>.rq
#     + images-<group>-url.txt, one triple per group (authors/novels/correspondents)
python3 scripts/build_images_query.py data/novels-authors-metadata-enriched.tsv \
        data/respondents-metadata-enriched.tsv

# 4. TEI -> index.html, with both data links handed to the stylesheet
xsltproc --stringparam wdqs-url    "$(head -1 wdqs-url.txt)" \
         --stringparam geojson-url "$(head -1 geojsonio-url.txt)" \
         --stringparam images-authors-url        "$(head -1 images-authors-url.txt)" \
         --stringparam images-novels-url         "$(head -1 images-novels-url.txt)" \
         --stringparam images-correspondents-url "$(head -1 images-correspondents-url.txt)" \
         -o index.html xslt/tei2html.xsl "$TEI"

# 5. schema.org metadata as a standalone file, lifted out of the page
python3 scripts/extract_jsonld.py index.html schema.jsonld

echo "index.html $(wc -c < index.html) B"

# 6. with "sh build.sh site": also collect the files as GitHub Pages will serve them
#    into _site/ (same list as .github/workflows/pages.yml), for a local preview:
#    python3 -m http.server 8000 -d _site
if [ "$1" = "site" ]; then
  mkdir -p _site
  cp index.html schema.jsonld query.rq ten-great-novels.graphml \
     "$TEI" data/novels-authors-metadata-enriched.tsv \
     data/respondents-metadata-enriched.tsv assets/favicon.svg _site/
  [ -f correspondents.geojson ] && cp correspondents.geojson _site/ || true
  echo "_site/ ready: python3 -m http.server 8000 -d _site"
fi
