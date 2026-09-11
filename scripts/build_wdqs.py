#!/usr/bin/env python3
"""
build_wdqs.py: reads the TEI file, counts the correspondents per place and
writes the SPARQL query behind the map link, plus the two links themselves.

The query is never executed by the build; it is handed to the stylesheet as a
link and kept as a file so that it stays readable and citable.

Usage: python3 scripts/build_wdqs.py data/ten-great-novels.xml
Writes: query.rq, wdqs-url.txt (line 1 = embed/auto-run, line 2 = editor)
"""
import sys, urllib.parse
from lxml import etree

from tei_places import count_places

INDENT = '   '                    # indentation of the VALUES block
WIDTH = 74                        # wrap it at this column
ENDPOINT = 'https://query.wikidata.org/'

counts = count_places(etree.parse(sys.argv[1]))
total = sum(counts.values())

# Wrap on pair boundaries, never inside a pair.
lines, current = [], ''
for qid, n in counts.most_common():
    pair = f'(wd:{qid} {n})'
    if len(INDENT) + len(current) + len(pair) + 1 > WIDTH:
        lines.append(current)
        current = ''
    current += ' ' + pair
values = '\n'.join(INDENT + line for line in lines + [current])

query = f"""#defaultView:Map
# Places of the correspondents in "Ten Great Novels" (Chicago 1891)
# {total} correspondents, {len(counts)} places, generated from the TEI edition
SELECT ?placeLabel ?correspondents ?coord {{
  VALUES (?place ?correspondents) {{
{values}
  }}
  ?place wdt:P625 ?coord
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
"""

open('query.rq', 'w').write(query)
encoded = urllib.parse.quote(query, safe='')
embed = f'{ENDPOINT}embed.html#{encoded}'          # runs the query straight away
editor = f'{ENDPOINT}#{encoded}'                   # opens it in the editor
open('wdqs-url.txt', 'w').write(f'{embed}\n{editor}\n')

print(f'{total} correspondents / {len(counts)} places | '
      f'query {len(query)} B | URL {len(embed)} B')
