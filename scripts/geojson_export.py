#!/usr/bin/env python3
"""
geojson_export.py: builds a GeoJSON of the correspondents' places and the
matching geojson.io link.

The counts come from the TEI file, the coordinates and names from Wikidata
(P625, fetched at build time through the wbgetentities API, one request for
all places, which is far less prone to throttling than the query service).
If Wikidata cannot be reached, the script writes an empty URL file and exits 0:
the build then simply omits the GeoJSON link instead of failing.

Usage: python3 scripts/geojson_export.py data/ten-great-novels.xml
Writes: correspondents.geojson, geojsonio-url.txt
"""
import json, sys, time, urllib.parse, urllib.request
from collections import Counter
from lxml import etree

N = '{http://www.tei-c.org/ns/1.0}'
API = 'https://www.wikidata.org/w/api.php'
UA = ('ten-great-novels-build/1.0 (https://github.com/lehkost/ten-great-novels; '
      'TEI edition build script) python-urllib')
CHUNK = 50                                  # wbgetentities takes 50 ids per call

# ---------------------------------------------------------------- counts
cnt = Counter()
for rs in etree.parse(sys.argv[1]).iter(N + 'rs'):
    if rs.get('type') != 'voter':
        continue
    # descendant axis: some places sit inside <orgName> ("Boston Public Schools")
    for pl in rs.iter(N + 'placeName'):
        if pl.get('ref'):
            cnt[pl.get('ref').rsplit('/', 1)[-1]] += 1

# ---------------------------------------------------------------- coordinates
def fetch(ids):
    q = urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(ids),
                                'props': 'labels|claims', 'languages': 'en',
                                'format': 'json', 'formatversion': '2'})
    req = urllib.request.Request(API + '?' + q, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)['entities']

def coordinate(entity):
    """Latitude/longitude of the preferred P625 statement, if any."""
    best = None
    for st in entity.get('claims', {}).get('P625', []):
        if st.get('rank') == 'deprecated':
            continue
        if best is None or st.get('rank') == 'preferred':
            best = st
    try:
        v = best['mainsnak']['datavalue']['value']
        return float(v['latitude']), float(v['longitude'])
    except (TypeError, KeyError):
        return None

ids = list(cnt)
coords = {}
try:
    for i in range(0, len(ids), CHUNK):
        chunk = ids[i:i + CHUNK]
        for attempt in range(3):
            try:
                entities = fetch(chunk)
                break
            except Exception:
                if attempt == 2:
                    raise
                time.sleep(2 * (attempt + 1))
        for q, e in entities.items():
            ll = coordinate(e)
            if ll:
                coords[q] = (e.get('labels', {}).get('en', {}).get('value', q), *ll)
except Exception as e:
    open('geojsonio-url.txt', 'w').write('\n')
    print(f'Wikidata not reachable ({e.__class__.__name__}: {e}); GeoJSON link omitted')
    sys.exit(0)

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
      + (f' | WITHOUT coordinates: {missing}' if missing else ''))
