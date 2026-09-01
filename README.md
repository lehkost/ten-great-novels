# Ten Great Novels

A TEI edition of *Ten Great Novels: Suggestions for Clubs and Private Reading*
(ed. Jenkin Lloyd Jones, Seventh Thousand, Chicago: Charles H. Kerr & Company, 1891),
a survey in which 72 correspondents named the ten novels they would recommend.

**Reading edition:** <https://lehkost.github.io/ten-great-novels/index.html>

## Published files

All of these live next to the reading edition, under
`https://lehkost.github.io/ten-great-novels/`:

| File | |
|---|---|
| `ten-great-novels.xml` | the TEI file |
| `ten-great-novels.graphml` | the votes as a bipartite network (70 correspondents, 143 novels, 700 edges) for Gephi, Cytoscape or networkx |
| `correspondents.geojson` | the 30 different places the correspondents wrote from, with the number of correspondents per place; coordinates from Wikidata |
| `query.rq` | the SPARQL query behind the map link, ready to paste into the Wikidata Query Service |
| `schema.jsonld` | schema.org metadata describing the edition and the data, also embedded in the page |

## Sources in this repository

| File | |
|---|---|
| `data/ten-great-novels.xml` | the TEI edition: the source of everything else |
| `xslt/tei2html.xsl` | XSLT 1.0 stylesheet producing the reading edition |
| `build.sh` | rebuilds the page and all data files |
| `scripts/consistency.py` | validates the annotation; exits non-zero on errors |
| `scripts/build_wdqs.py` | writes `query.rq` and the Wikidata Query Service link |
| `scripts/geojson_export.py` | writes `correspondents.geojson` and the geojson.io link |
| `scripts/tei2graphml.py` | writes the bipartite network of correspondents and votes |
| `scripts/extract_jsonld.py` | writes `schema.jsonld` from the metadata embedded in the page |
| `assets/favicon.svg` | site icon, copied to the root of the published site |
| `requirements.txt` | Python dependencies (lxml) |
| `CITATION.cff` | citation metadata |
| `.github/workflows/pages.yml` | checks, builds and deploys on every push |

The build products are not kept under version control: `index.html`,
`schema.jsonld`, `query.rq`, `correspondents.geojson` and
`ten-great-novels.graphml` are generated on every push and published to
GitHub Pages.

## Building locally

Requires `xsltproc` (Debian/Ubuntu: `apt install xsltproc`; macOS: preinstalled)
and the Python packages listed in `requirements.txt`:

    pip install -r requirements.txt
    python3 scripts/consistency.py data/ten-great-novels.xml
    sh build.sh

The counts come from the TEI file; the coordinates for the map are queried from
the Wikidata Query Service at build time. If that service cannot be reached, the
build still succeeds and the page simply omits the GeoJSON link.

Every push to `main` runs the same steps in GitHub Actions and deploys the result
to GitHub Pages.

## Tools

The TEI edition was encoded and annotated using the `<oXygen/>` XML Editor 28.1.

The tooling in `xslt/` and `scripts/` was drafted with Claude (Anthropic) in
September 2026 and is maintained by the editor.

## Licence

The encoding and annotation are released under CC0 1.0 Universal.
The 1891 text itself is in the public domain.
