# Ten Great Novels

A TEI edition of *Ten Great Novels: Suggestions for Clubs and Private Reading*
(ed. Jenkin Lloyd Jones, Seventh Thousand, Chicago: Charles H. Kerr & Company, 1891),
a survey in which 72 correspondents replied; 70 of them named the novels they would recommend
(two letters name none).

**Reading edition:** <https://lehkost.github.io/ten-great-novels/index.html>

## Published files

All of these live next to the reading edition, under
`https://lehkost.github.io/ten-great-novels/`.

Counts differ between derivatives: the edition contains 72 responses; the GraphML contains the
70 correspondents who cast at least one vote; the place data cover 71 correspondents with an
identified place (the anonymous response has none).

| File | |
|---|---|
| `ten-great-novels.xml` | the TEI file |
| `ten-great-novels.graphml` | the votes as a bipartite network (70 correspondents, 143 novels, 700 edges) for Gephi, Cytoscape or NetworkX; nodes carry Wikipedia sitelinks, QRank and (novels) Goodreads ratings, each with the date it was collected (see below) |
| `correspondents.geojson` | the 30 different places the correspondents wrote from, with the number of correspondents per place; coordinates from Wikidata |
| `query.rq` | the SPARQL query behind the map link, ready to paste into the Wikidata Query Service |
| `schema.jsonld` | schema.org metadata describing the edition and the data, also embedded in the page |
| `novels-authors-metadata-enriched.tsv` | one row per novel with Wikidata and Goodreads identifiers, plus Wikipedia sitelinks, QRank and Goodreads ratings |
| `respondents-metadata-enriched.tsv` | one row per correspondent with Wikidata identifier, gender, dates of life, Wikipedia sitelinks, QRank and the date and URL of the letter's first publication |

## Sources in this repository

| File | |
|---|---|
| `data/ten-great-novels.xml` | the TEI edition: the source of everything else |
| `data/novels-authors-metadata-enriched.tsv` | one row per novel, keyed by Wikidata Q-id: title, language, publication year, votes and mentions, author, author's gender, Goodreads id, and the enrichments (see below) |
| `data/respondents-metadata-enriched.tsv` | one row per correspondent (72, in the order of the letters): TEI id, name, Wikidata Q-id, gender, birth and death date, the enrichments, and where the letter was first printed (see below) |
| `xslt/tei2html.xsl` | XSLT 1.0 stylesheet producing the reading edition |
| `build.sh` | rebuilds the page and all data files |
| `scripts/consistency.py` | validates the annotation; exits non-zero on errors |
| `scripts/build_wdqs.py` | writes `query.rq` and the Wikidata Query Service link |
| `data/places-coordinates.tsv` | coordinates of the correspondents' places (Wikidata Q-id, name, latitude, longitude), fetched from Wikidata once and kept here so that the build works offline |
| `scripts/tei_places.py` | shared helper that counts the correspondents per place, used by `build_wdqs.py` and `geojson_export.py` |
| `scripts/build_images_query.py` | writes one Wikidata query per group (`images-authors.rq`, `images-novels.rq`, `images-correspondents.rq`), each showing one image (P18) for every item of that group, and the matching `images-<group>-url.txt` with the link that runs it in the Wikidata Query Service (line 1: result only, used by the page; line 2: editor); built from the two metadata tables, not published |
| `scripts/geojson_export.py` | writes `correspondents.geojson` and the geojson.io link |
| `scripts/tei2graphml.py` | writes the bipartite network of correspondents and votes, enriched from the two metadata tables |
| `scripts/extract_jsonld.py` | writes `schema.jsonld` from the metadata embedded in the page |
| `assets/favicon.svg` | site icon, copied to the root of the published site |
| `requirements.txt` | Python dependencies (lxml) |
| `CITATION.cff` | citation metadata |
| `.github/workflows/pages.yml` | checks, builds and deploys on every push |
| `.github/workflows/release.yml` | on a version tag (e.g. `1.0`): checks that the tag matches the version in the TEI header, builds and publishes a GitHub release with the data files |

### Columns of `novels-authors-metadata-enriched.tsv`

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
| `novel_wikipedia_sitelinks` | number of Wikipedia sitelinks of the novel's Wikidata item |
| `author_wikipedia_sitelinks` | number of Wikipedia sitelinks of the author's Wikidata item |
| `novel_qrank`, `author_qrank` | [QRank](https://qrank.toolforge.org/) of the Wikidata item; empty where the item has no QRank entry |
| `novel_goodreads_ratings` | number of ratings of the work on Goodreads; empty where there is no Goodreads record |
| `…_retrieved` | one column after each of the five enrichments above: the time (UTC, ISO 8601) at which that value was collected |

### Columns of `respondents-metadata-enriched.tsv`

| Column | |
|---|---|
| `respondent_number` | running number, in the order of the letters |
| `respondent_id` | `xml:id` of the correspondent in the TEI file (`voter-…`), also the node id in the GraphML file |
| `respondent_name` | name as given in the edition |
| `respondent_qid` | Wikidata Q-id; empty where the correspondent is not identified |
| `respondent_gender` | `female`, `male` or `unknown` |
| `respondent_birth_date`, `respondent_death_date` | dates from Wikidata, as far as known |
| `respondent_wikipedia_sitelinks` | number of Wikipedia sitelinks of the Wikidata item |
| `respondent_qrank` | QRank of the Wikidata item; empty where the item has no QRank entry |
| `respondent_wikipedia_sitelinks_retrieved`, `respondent_qrank_retrieved` | time (UTC) at which the value was collected |
| `respondent_letter_first_printed` | date of the periodical issue in which the letter was first printed |
| `respondent_letter_first_printed_url` | link to that issue |

### Enrichments

The columns for Wikipedia sitelinks, QRank and Goodreads ratings were added with the
[Canon Curator](https://github.com/temporal-communities/canon-curator). The data were
crawled on **21 September 2026**; each value carries its own retrieval time in the
neighbouring `…_retrieved` column. Sitelinks, QRank and ratings change over time, so
the values are a snapshot and are not updated by the build.

In `ten-great-novels.graphml` the same values are attached to the nodes. The day of the
collection is stated once per attribute, in the `<desc>` of its `<key>` declaration
(e.g. "QRank of the novel's Wikidata item; …; collected 2026-09-21, Canon Curator"), not on each value:

    <node id="work_Q102461080">
      <data key="label">Fredrika Bremer: The Neighbors (1837)</data>
      <data key="node_type">work</data>
      <data key="wikidata_id">Q102461080</data>
      <data key="novel_wikipedia_sitelinks">1</data>
      <data key="novel_qrank">0</data>
      <data key="novel_qrank_log10">0</data>
      <data key="novel_goodreads_ratings">116</data>
      <data key="language">Swedish</data>
    </node>

Novel nodes have `novel_wikipedia_sitelinks`, `novel_qrank`, `novel_qrank_log10`,
`novel_goodreads_ratings` and `novel_goodreads_ratings_log10`; correspondent nodes have `respondent_wikipedia_sitelinks`,
`respondent_qrank` and `respondent_qrank_log10`. A value that is empty in the table
(no Goodreads record, no Wikidata item) is left out of the node.

QRank and Goodreads ratings are treated differently, so that nodes can be sized by them (e.g.
in Gephi, which skips nodes without the attribute instead of making them smallest). Where the
table has no QRank for an item, or no Goodreads ratings for a novel (for example
"One of the Barchester Set", which stands for a series and has no single Goodreads record),
the node gets `0`: 0 means "not ranked", it is not a measurement. Both values span several
orders of magnitude, so each node also carries `…_qrank_log10` and
`novel_goodreads_ratings_log10` = log10(1 + value), which is 0 for the unranked. Size nodes by
the log10 columns for a readable scale (in the example, the novel has no QRank entry).

The author columns exist only in the TSV, since authors are not nodes of the network.

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

The counts come from the TEI file; the coordinates for the map come from
`data/places-coordinates.tsv`, a table of Wikidata Q-id, name, latitude and longitude
(P625) for every place a correspondent wrote from. Places missing from the table are
fetched from the Wikidata API and added to it, so a build needs network only the first time
(or after a new place has been annotated); commit the table when it changes. To refresh
the coordinates, delete the file and build again. If a fetch is needed and Wikidata cannot be
reached, the build still succeeds and the page simply omits the GeoJSON link.

Every push to `main` runs the same steps in GitHub Actions and deploys the result
to GitHub Pages.

## Tools

The TEI edition was encoded and annotated using the `<oXygen/>` XML Editor 28.1.

The tooling in `xslt/` and `scripts/` was drafted with Claude (Anthropic) in
September 2026 and is maintained by the editor.

## Licence

The encoding and annotation are released under CC0 1.0 Universal.
The 1891 text itself is in the public domain.
