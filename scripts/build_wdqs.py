#!/usr/bin/env python3
"""
build_wdqs.py: reads the TEI file, counts the correspondents per place and
writes the SPARQL query plus the two Wikidata Query Service links.

Usage: python3 build_wdqs.py ten-great-novels.xml
Writes: query.rq, wdqs-url.txt (line 1 = embed/auto-run, line 2 = editor)
"""
import sys, urllib.parse
from collections import Counter
from lxml import etree

N = '{http://www.tei-c.org/ns/1.0}'
tree = etree.parse(sys.argv[1])

# Level of extraction: the place of a correspondent is the <placeName ref="…">
# inside <rs type="voter">. Other placeNames in the file (circular letter,
# imprint) are not correspondents' places and stay out.
cnt = Counter()
for rs in tree.iter(N + 'rs'):
    if rs.get('type') != 'voter':
        continue
    # descendant axis: some places sit inside <orgName> ("Boston Public Schools")
    for pl in rs.iter(N + 'placeName'):
        if pl.get('ref'):
            cnt[pl.get('ref').rsplit('/', 1)[-1]] += 1

lines, cur = [], '   '            # wrap on pair boundaries, never inside a pair
for q, n in cnt.most_common():
    p = f'(wd:{q} {n})'
    if len(cur) + len(p) + 1 > 74:
        lines.append(cur); cur = '   '
    cur += ' ' + p
values = '\n'.join(lines + [cur])

query = f"""#defaultView:Map
# Places of the correspondents in "Ten Great Novels" (Chicago 1891)
# {sum(cnt.values())} correspondents, {len(cnt)} places, generated from the TEI edition
SELECT ?placeLabel ?correspondents ?coord {{
  VALUES (?place ?correspondents) {{
{values}
  }}
  ?place wdt:P625 ?coord
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}
"""

open('query.rq', 'w').write(query)
enc = urllib.parse.quote(query, safe='')
embed = 'https://query.wikidata.org/embed.html#' + enc
editor = 'https://query.wikidata.org/#' + enc
open('wdqs-url.txt', 'w').write(embed + '\n' + editor + '\n')
print(f'{sum(cnt.values())} correspondents / {len(cnt)} places | query {len(query)} B | URL {len(embed)} B')
