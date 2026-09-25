#!/usr/bin/env python3
"""
tei2graphml.py: turns the TEI edition of "Ten Great Novels" into a bipartite
network in GraphML format.

The nodes are correspondents (rs/@type="voter") and works (rs/@type="novel"). An
edge joins a correspondent to every work on the list they submitted, that is to
every rs/@ana="#vote". Correspondents who cast no votes get no node.

Node ids: the correspondent's xml:id ("voter-prof-c-c-everett"), and "work_" plus
the Wikidata Q number ("work_Q907568").

Correspondents carry their gender, taken from the @ana attribute of the TEI file,
and the number of Wikipedia sitelinks and the QRank of their Wikidata item, taken
from respondents-metadata-enriched.tsv (joined on the node id).
Works carry their language, the number of Wikipedia sitelinks and the QRank of
their Wikidata item and their number of Goodreads ratings, taken from
novels-authors-metadata-enriched.tsv, and their
label is framed there with the author's name and the year of publication:
"Friedrich Spielhagen: Hammer and Anvil (1869)". The title itself stays exactly
as the TEI file spells it; the table only supplies the frame, and the two are
joined on the Q number. Years arrive in EDTF and are rewritten for reading:
"1869" stays, "1678/1684" becomes "1678-1684", "0170~" becomes "c. AD 170".

The enrichment values (sitelinks, QRank, Goodreads ratings) carry the date they
were collected, the day of the "*_retrieved" timestamp in the table. It is written
once per attribute, in the <desc> of its <key> declaration (the place GraphML
provides for documentation), as a day or, if a value was collected over several
days, as a range:
    <key id="novel_qrank" ...><desc>QRank of ...; collected 2026-09-21, ...</desc></key>
A value that is empty in the table (no Goodreads record, no Wikidata item) is
left out.

QRank and Goodreads ratings are the exception: a node without a QRank entry, or a
novel without a Goodreads record (a series, say), gets the value 0, so that
programs which size nodes by an attribute (Gephi) put it at the bottom of the
scale instead of skipping it. 0 marks "not ranked", not a
measurement. Both span several orders of magnitude, so every node also carries
"novel_qrank_log10", "respondent_qrank_log10" and "novel_goodreads_ratings_log10"
= log10(1 + value), which is 0 for the unranked.

Usage:
    python3 scripts/tei2graphml.py data/ten-great-novels.xml ten-great-novels.graphml
The two tables are expected next to the TEI file; different paths can be given
as a third (novels) and a fourth (correspondents) argument.
"""

import collections
import csv
import math
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
METADATA = "novels-authors-metadata-enriched.tsv"
RESPONDENTS = "respondents-metadata-enriched.tsv"
# One source of truth: the node attributes are declared and written from this
# list, in this order, as (name, GraphML type). Fields listed in DATED come with
# the date of their collection, which goes into the <desc> of their <key>.
NODE_FIELDS = (
    ("label", "string"),
    ("node_type", "string"),
    ("wikidata_id", "string"),
    ("novel_wikipedia_sitelinks", "int"),
    ("novel_qrank", "long"),
    ("novel_qrank_log10", "double"),
    ("novel_goodreads_ratings", "int"),
    ("novel_goodreads_ratings_log10", "double"),
    ("respondent_wikipedia_sitelinks", "int"),
    ("respondent_qrank", "long"),
    ("respondent_qrank_log10", "double"),
    ("language", "string"),
    ("gender", "string"),
)
DATED = frozenset(name for name, _ in NODE_FIELDS
                  if name.endswith(("_sitelinks", "_qrank", "_qrank_log10", "_ratings", "_ratings_log10")))


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


def enrichment(row, field):
    """(value, date) of one enriched column; ("", "") when the table has none.

    The table names the columns "novel_qrank" and "novel_qrank_retrieved"; the
    date is the day part of the ISO timestamp in the second one."""
    value = (row.get(field) or "").strip()
    day = (row.get(field + "_retrieved") or "").strip()[:10]
    return (value, day) if value else ("", "")


def with_log(field, row):
    """{field, field_log10} as (value, date) pairs, for counts used to size nodes.

    A missing value becomes ("0", ""), without a date, since nothing was measured."""
    value, day = row.get(field) or ("", "")
    if not value:
        value, day = "0", ""
    log = f"{math.log10(1 + int(value)):.4f}".rstrip("0").rstrip(".") or "0"
    return {field: (value, day), field + "_log10": (log, day)}


def read_metadata(path):
    """{Q number: {language, author, year, enrichments}} from the novels table."""
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
                **{field: enrichment(row, field) for field in (
                    "novel_wikipedia_sitelinks", "novel_qrank",
                    "novel_goodreads_ratings")},
            }
    return meta


def read_respondents(path):
    """{xml:id: {sitelinks, qrank}} from respondents-metadata-enriched.tsv."""
    respondents = {}
    if not path or not os.path.exists(path):
        print(f"Note: {path} not found, GraphML without correspondent enrichments",
              file=sys.stderr)
        return respondents
    with open(path, encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="\t"):
            node_id = (row.get("respondent_id") or "").strip()
            if node_id:
                respondents[node_id] = {
                    field: enrichment(row, field) for field in (
                        "respondent_wikipedia_sitelinks", "respondent_qrank")}
    return respondents


def work_label(title, info):
    """Author and year around the title as the TEI file spells it."""
    label = f"{info['author']}: {title}" if info.get("author") else title
    return f"{label} ({info['year']})" if info.get("year") else label


def extract(root, meta=None, respondents=None):
    """Returns (voters, works, edges) for the votes that were cast."""
    meta = meta or {}
    respondents = respondents or {}
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
            **respondents.get(node_id, {}),
        }
        voters[node_id].update(with_log("respondent_qrank", voters[node_id]))
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
                    **{k: v for k, v in info.items() if k.startswith("novel_")},
                }
                for field in ("novel_qrank", "novel_goodreads_ratings"):
                    works[work_id].update(with_log(field, works[work_id]))
            edges[(node_id, work_id)] += 1

    return voters, works, edges


DESCRIPTIONS = {
    "novel_wikipedia_sitelinks": "Number of Wikipedia sitelinks of the novel's Wikidata item",
    "novel_qrank": "QRank of the novel's Wikidata item; 0 = no QRank entry (not ranked)",
    "novel_qrank_log10": "log10(1 + novel_qrank); 0 = not ranked",
    "novel_goodreads_ratings": "Number of ratings of the work on Goodreads; 0 = no Goodreads record for a single work (e.g. a series)",
    "novel_goodreads_ratings_log10": "log10(1 + novel_goodreads_ratings); 0 = no ratings",
    "respondent_wikipedia_sitelinks": "Number of Wikipedia sitelinks of the correspondent's Wikidata item",
    "respondent_qrank": "QRank of the correspondent's Wikidata item; 0 = no QRank entry (not ranked)",
    "respondent_qrank_log10": "log10(1 + respondent_qrank); 0 = not ranked",
}


def write_graphml(path, voters, works, edges):
    days = collections.defaultdict(set)     # field -> days on which it was collected
    body = []

    def node(node_id, data):
        body.append(f"    <node id={quoteattr(node_id)}>")
        for field, _ in NODE_FIELDS:
            value = data.get(field)
            if field in DATED:              # stored as (value, date)
                value, day = value or ("", "")
                if day:
                    days[field].add(day)
            if value:
                body.append(f"      <data key={quoteattr(field)}>{escape(value)}</data>")
        body.append("    </node>")

    for node_id in sorted(works):
        node(node_id, works[node_id])
    for node_id in sorted(voters):
        node(node_id, voters[node_id])
    for source, target in sorted(edges):
        body.append(f"    <edge source={quoteattr(source)} target={quoteattr(target)}>")
        body.append(f'      <data key="weight">{edges[(source, target)]:.1f}</data>')
        body.append("    </edge>")

    out = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<graphml xmlns="http://graphml.graphdrawing.org/xmlns">']
    for field, kind in NODE_FIELDS:
        head = f'  <key id="{field}" for="node" attr.name="{field}" attr.type="{kind}"'
        if field in DATED:
            # The date of the crawl is documented once per attribute, in the
            # <desc> the GraphML schema provides for keys, not on every value.
            when = "–".join(sorted(days[field])[::max(len(days[field]) - 1, 1)])
            text = DESCRIPTIONS[field] + (f"; collected {when}" if when else "")
            out += [head + ">",
                    f"    <desc>{escape(text)}, Canon Curator</desc>" if when else
                    f"    <desc>{escape(text)}</desc>",
                    "  </key>"]
        else:
            out.append(head + "/>")
    out += ['  <key id="weight" for="edge" attr.name="weight" attr.type="double"/>',
            '  <graph edgedefault="undirected">']
    out += body
    out += ["  </graph>", "</graphml>", ""]
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main(argv):
    if len(argv) not in (3, 4, 5):
        print(__doc__.strip(), file=sys.stderr)
        return 2
    folder = os.path.dirname(os.path.abspath(argv[1]))
    meta_path = argv[3] if len(argv) >= 4 else os.path.join(folder, METADATA)
    resp_path = argv[4] if len(argv) == 5 else os.path.join(folder, RESPONDENTS)
    voters, works, edges = extract(etree.parse(argv[1]).getroot(),
                                   read_metadata(meta_path),
                                   read_respondents(resp_path))
    write_graphml(argv[2], voters, works, edges)
    print(f"{argv[2]}: {len(voters)} correspondents + {len(works)} works = "
          f"{len(voters) + len(works)} nodes, {len(edges)} edges")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
