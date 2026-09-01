#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tei2graphml.py — erzeugt aus der TEI-Ausgabe von »Ten Great Novels« ein
bipartites Netzwerk im GraphML-Format.

Knoten sind Briefschreiber (rs/@type="voter") und Werke (rs/@type="novel").
Eine Kante verbindet einen Briefschreiber mit jedem Werk seiner abgegebenen
Liste, also mit jedem rs/@ana="#vote". Briefschreiber ohne Stimme bleiben
weg. Beschriftungen werden unverändert aus der TEI übernommen.

Knotenkennungen: die xml:id des Briefschreibers (»voter-everett-c-c«) und
»work_« plus Wikidata-Q-Nummer (»work_Q907568«).

Aufruf:
    python3 tei2graphml.py Ten_Great_Novels_1884.xml co-voting.graphml
"""

from __future__ import annotations

import collections
import re
import sys
from xml.sax.saxutils import escape, quoteattr

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"t": TEI}
T = "{%s}" % TEI
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
WD_PREFIX = "http://www.wikidata.org/entity/"


def text_of(el) -> str:
    """Reiner Textinhalt eines Elements, Leerraum normalisiert."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def qid_of(el) -> str:
    """Wikidata-Q-Nummer aus @ref, leer wenn nicht verknüpft."""
    ref = el.get("ref") or ""
    return ref[len(WD_PREFIX):] if ref.startswith(WD_PREFIX) else ""


def slugify(value: str) -> str:
    """Ersatzkennung für Werke ohne Wikidata-Verweis."""
    value = re.sub(r"[^a-z0-9]+", "-", value.lower().replace("ß", "ss"))
    return value.strip("-") or "unnamed"


def extract(root):
    """Liefert (voters, works, edges) für die abgegebenen Stimmen."""
    # Werkbeschriftung: die im Band häufigste Schreibung, über das ganze
    # Dokument ermittelt, damit auch der Abstimmungsteil mitzählt.
    forms = collections.defaultdict(collections.Counter)
    for rs in root.iter(T + "rs"):
        if rs.get("type") == "novel":
            label = text_of(rs)
            forms[qid_of(rs) or "~" + slugify(label)][label] += 1

    voters, works, edges = {}, {}, collections.Counter()

    for div in root.findall('.//t:div[@type="response"]', NS):
        rs_voter = next((e for e in div.iter(T + "rs")
                         if e.get("type") == "voter"), None)
        if rs_voter is None:
            continue
        node_id = rs_voter.get(XML_ID)
        if not node_id:
            print("Warnung: Brief %s ohne xml:id am voter-Element" % div.get("n"),
                  file=sys.stderr)
            continue

        votes = []
        for rs in div.iter(T + "rs"):
            if rs.get("type") != "novel" or rs.get("ana") != "#vote":
                continue
            if rs.get("prev"):          # Fortsetzung eines geteilten Titels
                continue
            key = qid_of(rs) or "~" + slugify(text_of(rs))
            votes.append(key)

        if not votes:                   # ohne Stimme kein Knoten
            continue

        pers = rs_voter.find("t:persName", NS)
        voters[node_id] = {
            "label": text_of(pers) if pers is not None else text_of(rs_voter),
            "node_type": "voter",
            "wikidata_id": qid_of(rs_voter),
        }
        for key in votes:
            work_id = "work_" + (key if key.startswith("Q") else key[1:])
            if work_id not in works:
                works[work_id] = {
                    "label": forms[key].most_common(1)[0][0],
                    "node_type": "work",
                    "wikidata_id": key if key.startswith("Q") else "",
                }
            edges[(node_id, work_id)] += 1

    return voters, works, edges


def write_graphml(path, voters, works, edges):
    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">',
        '  <key id="label" for="node" attr.name="label" attr.type="string"/>',
        '  <key id="node_type" for="node" attr.name="node_type" attr.type="string"/>',
        '  <key id="wikidata_id" for="node" attr.name="wikidata_id" attr.type="string"/>',
        '  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
        '  <graph edgedefault="undirected">',
    ]

    def node(node_id, data):
        out.append("    <node id=%s>" % quoteattr(node_id))
        for field in ("label", "node_type", "wikidata_id"):
            if data.get(field):
                out.append("      <data key=%s>%s</data>"
                           % (quoteattr(field), escape(data[field])))
        out.append("    </node>")

    for node_id in sorted(works):
        node(node_id, works[node_id])
    for node_id in sorted(voters):
        node(node_id, voters[node_id])
    for source, target in sorted(edges):
        out.append("    <edge source=%s target=%s>"
                   % (quoteattr(source), quoteattr(target)))
        out.append('      <data key="weight">%.1f</data>' % edges[(source, target)])
        out.append("    </edge>")
    out += ["  </graph>", "</graphml>", ""]
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main(argv):
    if len(argv) != 3:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    voters, works, edges = extract(etree.parse(argv[1]).getroot())
    write_graphml(argv[2], voters, works, edges)
    print("%s: %d Briefschreiber + %d Werke = %d Knoten, %d Kanten"
          % (argv[2], len(voters), len(works),
             len(voters) + len(works), len(edges)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
