#!/usr/bin/env python3
"""
geojson_export.py: builds a GeoJSON of the correspondents' places and the
matching geojson.io link.

The counts come from the TEI file, the coordinates and names from Wikidata
(P625, queried at build time). If the query service cannot be reached, the
script writes an empty URL file and exits 0: the build then simply omits the
GeoJSON link instead of failing.

Usage: python3 geojson_export.py ten-great-novels.xml
Writes: correspondents.geojson, geojsonio-url.txt
"""
import json, sys, urllib.parse, urllib.request, urllib.error
from collections import Counter
from lxml import etree

N = '{http://www.tei-c.org/ns/1.0}'
ENDPOINT = 'https://query.wikidata.org/sparql'
UA = ('ten-great-novels-build/1.0 (https://github.com/lehkost/ten-great-novels; '
      'TEI edition build script) python-urllib')

# ---------------------------------------------------------------- counts
cnt = Counter()
for rs in etree.parse(sys.argv[1]).iter(N + 'rs'):
    if rs.get('type') != 'voter':
        continue
    # descendant axis: some places sit inside <orgName> ("Boston Public Schools")
    for pl in rs.iter(N + 'placeName'):
        if pl.get('ref'):
            cnt[pl.get('ref').rsplit('/', 1)[-1]] += 1

values = ' '.join('wd:' + q for q in cnt)
query = f"""SELECT ?place ?placeLabel ?lat ?lon WHERE {{
  VALUES ?place {{ {values} }}
  ?place p:P625/psv:P625 ?node .
  ?node wikibase:geoLatitude ?lat ; wikibase:geoLongitude ?lon .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en" }}
}}"""

# ---------------------------------------------------------------- coordinates
def fetch():
    url = ENDPOINT + '?' + urllib.parse.urlencode({'query': query, 'format': 'json'})
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)['results']['bindings']

try:
    rows = fetch()
except Exception as e:                      # network, timeout, rate limit, outage
    open('geojsonio-url.txt', 'w').write('\n')
    print(f'Wikidata not reachable ({e.__class__.__name__}); GeoJSON link omitted')
    sys.exit(0)

coords = {}
for b in rows:
    q = b['place']['value'].rsplit('/', 1)[-1]
    coords[q] = (b['placeLabel']['value'], float(b['lat']['value']), float(b['lon']['value']))

missing = [q for q in cnt if q not in coords]

# ---------------------------------------------------------------- output
def colour(n):
    return ('bd0026' if n >= 10 else 'f03b20' if n >= 5 else
            'fd8d3c' if n >= 3 else 'feb24c' if n == 2 else 'ffeda0')

feats = []
for q, n in cnt.most_common():
    if q not in coords:
        continue
    name, lat, lon = coords[q]
    p = {'name': name, 'wikidata': q, 'correspondents': n,
         'marker-color': '#' + colour(n),
         'marker-size': 'large' if n >= 5 else 'medium' if n >= 2 else 'small'}
    if 1 <= n <= 9:                          # simplestyle shows a single digit in the pin
        p['marker-symbol'] = str(n)
    feats.append({'type': 'Feature',
                  'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                  'properties': p})

fc = {'type': 'FeatureCollection', 'features': feats}
open('correspondents.geojson', 'w').write(json.dumps(fc, indent=1) + '\n')

# For the URL the colours are written WITHOUT the leading '#': geojson.io decodes
# the fragment and then splits it again on '#', so a %23 truncates the JSON.
url_fc = json.loads(json.dumps(fc))
for f in url_fc['features']:
    f['properties']['marker-color'] = f['properties']['marker-color'].lstrip('#')
compact = json.dumps(url_fc, separators=(',', ':'))
assert '#' not in compact, 'payload must not contain a literal #'
open('geojsonio-url.txt', 'w').write(
    'https://geojson.io/#data=data:application/json,' + urllib.parse.quote(compact, safe='') + '\n')

print(f'{len(feats)} places from Wikidata, {sum(cnt.values())} correspondents'
      + (f' | WITHOUT coordinates in Wikidata: {missing}' if missing else ''))
