#!/usr/bin/env python3
"""
extract_jsonld.py: lifts the schema.org block out of the rendered page and
writes it as a standalone file.

The metadata are produced once, by the stylesheet, and embedded in index.html
where search engines read them. This script only copies that block out, so the
file and the page can never disagree. It also parses the JSON, which turns a
malformed block into a build failure instead of silent breakage.

Usage: python3 scripts/extract_jsonld.py index.html schema.jsonld
"""
import json, re, sys

html = open(sys.argv[1], encoding='utf-8').read()
m = re.search(r'<script type="application/ld\+json">(.*?)</script>', html, re.S)
if not m:
    sys.exit('no schema.org block found in ' + sys.argv[1])

data = json.loads(m.group(1))          # raises on malformed JSON
open(sys.argv[2], 'w', encoding='utf-8').write(
    json.dumps(data, indent=1, ensure_ascii=False) + '\n')

nodes = data.get('@graph', [data])
print(f"{sys.argv[2]}: {len(nodes)} nodes ({', '.join(n['@type'] for n in nodes)})")
