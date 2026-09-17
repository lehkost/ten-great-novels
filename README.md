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
| `novels-authors-metadata.tsv` | one row per novel with Wikidata and Goodreads identifiers |

## Sources in this repository

| File | |
|---|---|
| `data/ten-great-novels.xml` | the TEI edition: the source of everything else |
| `data/novels-authors-metadata.tsv` | one row per novel, keyed by Wikidata Q-id: title, language, publication year, votes and mentions, author, author's gender, Goodreads id (see below) |
| `xslt/tei2html.xsl` | XSLT 1.0 stylesheet producing the reading edition |
| `build.sh` | rebuilds the page and all data files |
| `scripts/consistency.py` | validates the annotation; exits non-zero on errors |
| `scripts/build_wdqs.py` | writes `query.rq` and the Wikidata Query Service link |
| `scripts/geojson_export.py` | writes `correspondents.geojson` and the geojson.io link |
| `scripts/tei2graphml.py` | writes the bipartite network of correspondents and votes, enriched from the metadata table |
| `scripts/extract_jsonld.py` | writes `schema.jsonld` from the metadata embedded in the page |
| `assets/favicon.svg` | site icon, copied to the root of the published site |
| `requirements.txt` | Python dependencies (lxml) |
| `CITATION.cff` | citation metadata |
| `.github/workflows/pages.yml` | checks, builds and deploys on every push |
| `.github/workflows/release.yml` | on a version tag (e.g. `1.0`): checks that the tag matches the version in the TEI header, builds and publishes a GitHub release with the data files |

### Columns of `novels-authors-metadata.tsv`

| Column | |
|---|---|
| `novel_qid` | Wikidata Q-id of the novel, the key used in the TEI file |
| `novel_title` | title as given in Wikidata |
| `novel_language` | original language |
| `novel_publication_year` | year of first publication, in EDTF (`1795/1796`, `0170~`) |
| `novel_vote_count` | votes in the letters (`ana="#vote"`) |
| `novel_mention_count` | mentions in the letters (`ana="#mention"`) |
| `author_qid` | Wikidata Q-id of the author |
| `author_name` | name of the author |
| `author_sex` | sex or gender of the author, as recorded in Wikidata |
| `novel_goodreads_id` | Goodreads work id (`https://www.goodreads.com/work/editions/<id>`); empty where no single Goodreads record exists |

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

The counts come from the TEI file; the coordinates for the map are fetched from
the Wikidata API at build time. If Wikidata cannot be reached, the build still
succeeds and the page simply omits the GeoJSON link.

Every push to `main` runs the same steps in GitHub Actions and deploys the result
to GitHub Pages.

## Tools

The TEI edition was encoded and annotated using the `<oXygen/>` XML Editor 28.1.

The tooling in `xslt/` and `scripts/` was drafted with Claude (Anthropic) in
September 2026 and is maintained by the editor.

## Licence

The encoding and annotation are released under CC0 1.0 Universal.
The 1891 text itself is in the public domain.
