#!/usr/bin/env python3
"""
geojson_export.py: builds a GeoJSON of the correspondents' places and the
matching geojson.io link.

The counts come from the TEI file, the coordinates and names from Wikidata
(P625, fetched through the wbgetentities API, one request for all places, which
is far less prone to throttling than the query service).

The coordinates are kept in data/places-coordinates.tsv, next to the TEI file.
Places found there are not asked for again, so a build needs no network as long
as every place of the TEI file is in the table. Places that are missing are
fetched from Wikidata and added to the table; commit the table when it changes.
To refresh it, delete the file (or single rows) and build again with network.
If a fetch is needed and Wikidata cannot be reached, the script writes an empty
URL file and exits 0: the build then simply omits the GeoJSON link instead of
failing.

Usage: python3 scripts/geojson_export.py data/ten-great-novels.xml
Writes: correspondents.geojson, geojsonio-url.txt
"""
import csv, json, os, sys, time, urllib.parse, urllib.request
from lxml import etree

from tei_places import count_places

N = '{http://www.tei-c.org/ns/1.0}'
API = 'https://www.wikidata.org/w/api.php'
UA = ('ten-great-novels-build/1.0 (https://github.com/lehkost/ten-great-novels; '
      'TEI edition build script) python-urllib')
CHUNK = 50                                  # wbgetentities takes 50 ids per call
RETRIES = 3
LANGUAGES = ('en', 'mul')                   # mul: Wikidata's language-neutral label
CACHE_NAME = 'places-coordinates.tsv'
CACHE_FIELDS = ('wikidata', 'name', 'latitude', 'longitude')

# ---------------------------------------------------------------- counts
cnt = count_places(etree.parse(sys.argv[1]))

# ---------------------------------------------------------------- coordinates
def fetch(ids):
    q = urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(ids),
                                'props': 'labels|claims',
                                'languages': '|'.join(LANGUAGES),
                                'format': 'json', 'formatversion': '2'})
    req = urllib.request.Request(API + '?' + q, headers={'User-Agent': UA})
    for attempt in range(RETRIES):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)['entities']
        except Exception:
            if attempt == RETRIES - 1:
                raise
            time.sleep(2 * (attempt + 1))

def label(entity, fallback):
    """English label, else the language-neutral one, else the Q number."""
    labels = entity.get('labels', {})
    for code in LANGUAGES:
        if labels.get(code, {}).get('value'):
            return labels[code]['value']
    return fallback

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

cache_path = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])), CACHE_NAME)

def read_cache(path):
    """{Q number: (name, latitude, longitude)} from the table, empty if absent."""
    if not os.path.exists(path):
        return {}
    with open(path, encoding='utf-8', newline='') as fh:
        return {r['wikidata']: (r['name'], float(r['latitude']), float(r['longitude']))
                for r in csv.DictReader(fh, delimiter='\t')}

def write_cache(path, table):
    with open(path, 'w', encoding='utf-8', newline='') as fh:
        w = csv.writer(fh, delimiter='\t', lineterminator='\n')
        w.writerow(CACHE_FIELDS)
        for q in sorted(table, key=lambda k: int(k[1:])):
            name, lat, lon = table[q]
            w.writerow((q, name, lat, lon))

table = read_cache(cache_path)
coords = {q: table[q] for q in cnt if q in table}
to_fetch = [q for q in cnt if q not in coords]
try:
    for i in range(0, len(to_fetch), CHUNK):
        for q, e in fetch(to_fetch[i:i + CHUNK]).items():
            ll = coordinate(e)
            if ll:
                coords[q] = (label(e, q), *ll)
except Exception as e:
    open('geojsonio-url.txt', 'w').write('\n')
    print(f'Wikidata not reachable ({e.__class__.__name__}: {e}); GeoJSON link omitted')
    sys.exit(0)

if to_fetch and any(q in coords for q in to_fetch):
    table.update({q: coords[q] for q in to_fetch if q in coords})
    write_cache(cache_path, table)
    print(f'{CACHE_NAME} updated ({sum(q in coords for q in to_fetch)} places): please commit it')

missing = [q for q in cnt if q not in coords]

# ---------------------------------------------------------------- output
def style(n):
    """simplestyle properties for a place named by n correspondents."""
    colour = ('bd0026' if n >= 10 else 'f03b20' if n >= 5 else
              'fd8d3c' if n >= 3 else 'feb24c' if n == 2 else 'ffeda0')
    size = 'large' if n >= 5 else 'medium' if n >= 2 else 'small'
    props = {'marker-color': '#' + colour, 'marker-size': size}
    if 1 <= n <= 9:                          # simplestyle shows a single digit in the pin
        props['marker-symbol'] = str(n)
    return props

feats = []
for q, n in cnt.most_common():
    if q not in coords:
        continue
    name, lat, lon = coords[q]
    feats.append({'type': 'Feature',
                  'geometry': {'type': 'Point', 'coordinates': [lon, lat]},
                  'properties': {'name': name, 'wikidata': q,
                                 'correspondents': n, **style(n)}})

fc = {'type': 'FeatureCollection', 'features': feats}
open('correspondents.geojson', 'w').write(json.dumps(fc, indent=1) + '\n')

# The file is written; the URL variant needs the same data with the colours
# WITHOUT the leading '#': geojson.io decodes the fragment and then splits it
# again on '#', so a %23 in the payload truncates the JSON.
for f in feats:
    f['properties']['marker-color'] = f['properties']['marker-color'].lstrip('#')
compact = json.dumps(fc, separators=(',', ':'))
assert '#' not in compact, 'payload must not contain a literal #'
open('geojsonio-url.txt', 'w').write(
    'https://geojson.io/#data=data:application/json,' + urllib.parse.quote(compact, safe='') + '\n')

print(f'{len(feats)} places ({len(cnt) - len(to_fetch)} from {CACHE_NAME}, {len(to_fetch) - len(missing)} from Wikidata), {sum(cnt.values())} correspondents'
      + (f' | WITHOUT coordinates: {missing}' if missing else ''))
