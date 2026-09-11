#!/usr/bin/env python3
"""
tei_places.py: shared helper for the two scripts that map the correspondents.

Both build_wdqs.py and geojson_export.py have to agree on which places count,
and they got it wrong once before: when a place moved inside <orgName>, one
script followed and the other did not, so the map and the query disagreed.
Keeping the rule in one place is what this module is for.
"""
from collections import Counter

TEI = '{http://www.tei-c.org/ns/1.0}'


def count_places(tree):
    """{Q number: number of correspondents} for the places they wrote from.

    A correspondent's place is a <placeName ref="…"> anywhere inside their
    <rs type="voter"> – the descendant axis matters, because some places sit
    inside an <orgName> ("Boston Public Schools"). Other placeNames in the file,
    in the circular letter and in the imprint, are not correspondents' places
    and stay out.
    """
    counts = Counter()
    for rs in tree.iter(TEI + 'rs'):
        if rs.get('type') != 'voter':
            continue
        for place in rs.iter(TEI + 'placeName'):
            if place.get('ref'):
                counts[place.get('ref').rsplit('/', 1)[-1]] += 1
    return counts
