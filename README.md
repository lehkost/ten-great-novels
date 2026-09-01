# Ten Great Novels

A TEI edition of *Ten Great Novels: Suggestions for Clubs and Private Reading*
(ed. Jenkin Lloyd Jones, Seventh Thousand, Chicago: Charles H. Kerr & Company, 1891),
a survey in which 72 correspondents named the ten novels they would recommend.

**Reading edition:** <https://lehkost.github.io/ten-great-novels/index.html>

## Sources in this repository

| File | |
|---|---|
| `ten-great-novels.xml` | the TEI edition — the source of everything else |
| `tei2html.xsl` | XSLT 1.0 stylesheet producing the reading edition |
| `build.sh` | rebuilds the page and all data files |
| `consistency.py` | validates the annotation; exits non-zero on errors |
| `build_wdqs.py` | writes `query.rq` and the Wikidata Query Service link |
| `geojson_export.py` | writes `correspondents.geojson` and the geojson.io link |
| `tei2graphml.py` | writes the bipartite network of correspondents and votes |

Nothing else is kept under version control. `index.html`, `query.rq`,
`correspondents.geojson` and `ten-great-novels.graphml` are build products;
they are generated on every push and published to GitHub Pages.

## Building locally

Requires `xsltproc` and Python 3 with `lxml`. The counts come from the TEI file;
the coordinates for the map are queried from the Wikidata Query Service at build
time. If that service cannot be reached, the build still succeeds and the page
simply omits the GeoJSON link.

    python3 consistency.py ten-great-novels.xml
    sh build.sh

Every push to `main` runs the same two steps in GitHub Actions and deploys the
result to GitHub Pages.

## Licence

The encoding and annotation are released under CC0 1.0 Universal.
The 1891 text itself is in the public domain.
