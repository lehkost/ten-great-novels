#!/usr/bin/env python3
"""
build_images_query.py: writes three Wikidata queries, one per group, each
showing one image (P18) for every author, every novel and every correspondent
of the edition.

The Q-ids come from the two metadata tables (authors and novels from
novels-authors-metadata-enriched.tsv, correspondents from
respondents-metadata-enriched.tsv). Only items that have an image are shown.
If an item has several images, one of them is picked (SAMPLE).

Each query is kept as its own file and as a link that runs it straight away in
the Wikidata Query Service; the three links are meant to sit on the words
"authors", "novels" and "correspondents" on the page. Running such a query
takes the query service a while (looking up ~70-160 items and adding a label
to each); it can run into the service's time limit when the service is busy.

Usage: python3 scripts/build_images_query.py data/novels-authors-metadata-enriched.tsv \\
           data/respondents-metadata-enriched.tsv
Writes, for each of authors/novels/correspondents:
    images-<group>.rq, images-<group>-url.txt (line 1 = embed/auto-run, line 2 = editor)
"""
import csv, sys, urllib.parse

ENDPOINT = 'https://query.wikidata.org/'
INDENT = '    '            # indentation of the VALUES block
WIDTH = 86                 # wrap it at this column
# (file/param slug, column of the table, human label for the query's comment)
GROUPS = (('authors', 'author_qid', 'authors'),
          ('novels', 'novel_qid', 'novels'),
          ('correspondents', 'respondent_qid', 'correspondents'))


def column(path, name):
    """Distinct Q-ids of one column of a table, in order of first appearance.

    The same author appears in the novels table once per novel, so duplicates
    are dropped; empty cells (e.g. the anonymous correspondent) are skipped."""
    seen = {}
    with open(path, encoding='utf-8', newline='') as fh:
        for row in csv.DictReader(fh, delimiter='\t'):
            q = (row.get(name) or '').strip()
            if q.startswith('Q') and q[1:].isdigit():
                seen.setdefault(q, None)          # a dict keeps the order
    return list(seen)


def wrap(pairs):
    """Joins the items with spaces and wraps the lines at WIDTH, never inside an item."""
    lines, current = [], ''
    for pair in pairs:
        if len(INDENT) + len(current) + len(pair) + 1 > WIDTH:
            lines.append(current)
            current = ''
        current += ' ' + pair
    return '\n'.join(INDENT + line for line in lines + [current])


novels_tsv, respondents_tsv = sys.argv[1], sys.argv[2]
tables = {'author_qid': novels_tsv, 'novel_qid': novels_tsv,
          'respondent_qid': respondents_tsv}

report = []
for slug, field, label in GROUPS:
    qids = column(tables[field], field)
    values = wrap(f'wd:{q}' for q in qids)

    # A plain image grid of one group: no ranks or headings are needed, since
    # each query covers only its own group. The image statement sits right
    # after the VALUES list, so the query service looks up the images of the
    # listed items only, instead of scanning every P18 statement on Wikidata
    # first (which, tried once, ran into a timeout).
    query = f"""#defaultView:ImageGrid
# One image (P18) for each of the {len(qids)} {label} of "Ten Great Novels"
# generated from the metadata tables; only items with an image are shown.
SELECT ?item ?itemLabel ?image WHERE {{
  VALUES ?item {{
{values}
  }}
  ?item wdt:P18 ?image .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
ORDER BY ?itemLabel
"""
    open(f'images-{slug}.rq', 'w').write(query)
    # The whole query is put after the # of the link and percent-encoded. With
    # embed.html the service shows only the result and runs the query at once;
    # the second link opens the same query in the editor.
    encoded = urllib.parse.quote(query, safe='')
    embed = f'{ENDPOINT}embed.html#{encoded}'
    editor = f'{ENDPOINT}#{encoded}'
    open(f'images-{slug}-url.txt', 'w').write(f'{embed}\n{editor}\n')
    report.append(f'{slug}: {len(qids)} items, {len(query)} B, URL {len(embed)} B')

print('images-{authors,novels,correspondents}.rq: ' + ' | '.join(report))
