#!/usr/bin/env python3
"""
tei2graphml.py: turns the TEI edition of "Ten Great Novels" into a bipartite
network in GraphML format.

The nodes are correspondents (rs/@type="voter") and works (rs/@type="novel"). An
edge joins a correspondent to every work on the list they submitted, that is to
every rs/@ana="#vote". Correspondents who cast no votes get no node.

Node ids: the correspondent's xml:id ("voter-prof-c-c-everett"), and "work_" plus
the Wikidata Q number ("work_Q907568").

Correspondents carry their gender, taken from the @ana attribute of the TEI file.
Works carry their language, taken from novels-authors-metadata.tsv, and their
label is framed there with the author's name and the year of publication:
"Friedrich Spielhagen: Hammer and Anvil (1869)". The title itself stays exactly
as the TEI file spells it; the table only supplies the frame, and the two are
joined on the Q number. Years arrive in EDTF and are rewritten for reading:
"1869" stays, "1678/1684" becomes "1678-1684", "0170~" becomes "c. AD 170".

Usage:
    python3 scripts/tei2graphml.py data/ten-great-novels.xml ten-great-novels.graphml
The metadata table is expected next to the TEI file; a different path can be
given as a third argument.
"""

import collections
import csv
import os
import re
import sys
from xml.sax.saxutils import escape, quoteattr

from lxml import etree

TEI = "http://www.tei-c.org/ns/1.0"
NS = {"t": TEI}
T = "{%s}" % TEI
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
WD_PREFIX = "http://www.wikidata.org/entity/"
METADATA = "novels-authors-metadata.tsv"
# One source of truth: the node attributes are declared and written from this list.
NODE_FIELDS = ("label", "node_type", "wikidata_id", "language", "gender")


def text_of(el) -> str:
    """Plain text content of an element, whitespace normalized."""
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def qid_of(el) -> str:
    """Wikidata Q number from @ref, empty when the element is not linked."""
    ref = el.get("ref") or ""
    return ref[len(WD_PREFIX):] if ref.startswith(WD_PREFIX) else ""


def slugify(value: str) -> str:
    """Substitute id for works without a Wikidata reference."""
    value = re.sub(r"[^a-z0-9]+", "-", value.lower().replace("ß", "ss"))
    return value.strip("-") or "unnamed"


def edtf_year(value: str) -> str:
    """EDTF year in reading form: 1869 | 1678-1684 | c. AD 170."""
    value = (value or "").strip()
    if not value:
        return ""
    if "/" in value:                       # interval: 1678/1684
        parts = [edtf_year(p) for p in value.split("/", 1)]
        return "–".join(p for p in parts if p)
    approx = value.endswith(("~", "?", "%"))
    digits = value.rstrip("~?%")
    if not digits.lstrip("-").isdigit():
        return value                       # unknown form, passed through unchanged
    year = int(digits)
    text = f"AD {year}" if 0 < year < 1000 else str(year)
    return f"c. {text}" if approx else text


def read_metadata(path):
    """{Q number: {language, author, year}} from novels-authors-metadata.tsv."""
    meta = {}
    if not path or not os.path.exists(path):
        print(f"Note: {path} not found, GraphML without language, author and year",
              file=sys.stderr)
        return meta
    with open(path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            qid = (row.get("novel_qid") or "").strip()
            if not qid:
                continue
            meta[qid] = {
                "language": (row.get("novel_language") or "").strip(),
                "author": (row.get("author_name") or "").strip(),
                "year": edtf_year(row.get("novel_publication_year")),
            }
    return meta


def work_label(title, info):
    """Author and year around the title as the TEI file spells it."""
    label = f"{info['author']}: {title}" if info.get("author") else title
    return f"{label} ({info['year']})" if info.get("year") else label


def extract(root, meta=None):
    """Returns (voters, works, edges) for the votes that were cast."""
    meta = meta or {}
    # Label of a work: its most frequent spelling, counted across the whole
    # document so that the printed tally has a say as well.
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
            print(f"Warning: letter {div.get('n')} has no xml:id on its voter element",
                  file=sys.stderr)
            continue

        votes = []
        for rs in div.iter(T + "rs"):
            if rs.get("type") != "novel" or rs.get("ana") != "#vote":
                continue
            if rs.get("prev"):          # continuation of a title split by a page break
                continue
            votes.append(qid_of(rs) or "~" + slugify(text_of(rs)))

        if not votes:                   # no vote, no node
            continue

        pers = rs_voter.find("t:persName", NS)
        voters[node_id] = {
            "label": text_of(pers) if pers is not None else text_of(rs_voter),
            "node_type": "voter",
            "wikidata_id": qid_of(rs_voter),
            "gender": (rs_voter.get("ana") or "").lstrip("#"),
        }
        for key in votes:
            linked = key.startswith("Q")
            work_id = "work_" + (key if linked else key[1:])
            if work_id not in works:
                info = meta.get(key, {}) if linked else {}
                works[work_id] = {
                    "label": work_label(forms[key].most_common(1)[0][0], info),
                    "node_type": "work",
                    "wikidata_id": key if linked else "",
                    "language": info.get("language", ""),
                }
            edges[(node_id, work_id)] += 1

    return voters, works, edges


def write_graphml(path, voters, works, edges):
    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
    out += [f'  <key id="{f}" for="node" attr.name="{f}" attr.type="string"/>'
            for f in NODE_FIELDS]
    out += ['  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
            '  <graph edgedefault="undirected">']

    def node(node_id, data):
        out.append(f"    <node id={quoteattr(node_id)}>")
        for field in NODE_FIELDS:
            if data.get(field):
                out.append(f"      <data key={quoteattr(field)}>"
                           f"{escape(data[field])}</data>")
        out.append("    </node>")

    for node_id in sorted(works):
        node(node_id, works[node_id])
    for node_id in sorted(voters):
        node(node_id, voters[node_id])
    for source, target in sorted(edges):
        out.append(f"    <edge source={quoteattr(source)} target={quoteattr(target)}>")
        out.append(f'      <data key="weight">{edges[(source, target)]:.1f}</data>')
        out.append("    </edge>")
    out += ["  </graph>", "</graphml>", ""]
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main(argv):
    if len(argv) not in (3, 4):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    meta_path = argv[3] if len(argv) == 4 else os.path.join(
        os.path.dirname(os.path.abspath(argv[1])), METADATA)
    voters, works, edges = extract(etree.parse(argv[1]).getroot(),
                                   read_metadata(meta_path))
    write_graphml(argv[2], voters, works, edges)
    print(f"{argv[2]}: {len(voters)} correspondents + {len(works)} works = "
          f"{len(voters) + len(works)} nodes, {len(edges)} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
