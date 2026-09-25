#!/usr/bin/env python3
"""
consistency.py: checks the annotation of the "Ten Great Novels" TEI edition.

A schema can say whether an element is allowed where it stands; these checks say
whether the annotation holds together: whether the same title always carries the
same Wikidata id, whether every letter has exactly one correspondent, whether the
recorded votes match the printed tally. Notes are informational; errors make the
script exit with 1, which stops the build before a faulty file is published.

Usage: python3 scripts/consistency.py data/ten-great-novels.xml
"""
import re, collections, sys
from lxml import etree
NS={'t':'http://www.tei-c.org/ns/1.0'}; T='{http://www.tei-c.org/ns/1.0}'
XML='{http://www.w3.org/XML/1998/namespace}'
WDRX=re.compile(r'^http://www\.wikidata\.org/entity/Q\d+$')
r=etree.parse(sys.argv[1]).getroot()
def tx(e): return re.sub(r'\s+',' ',''.join(e.itertext())).strip()
def norm(t): return re.sub(r'[""\'`,.!?]','',re.sub(r'^(the|a|an) ','',t.lower().strip(' ,.;'))).strip()
def sect(e):
    for a in e.iterancestors(T+'div'):
        if a.get('type') in ('vote','votegroup','letters','question','preface'): return a.get('type')
    return 'front'
OK,WARN,ERR=[],[],[]
def ok(m): OK.append(m)
def warn(m): WARN.append(m)
def err(m): ERR.append(m)

RS=[e for e in r.iter(T+'rs')]
NOV=[e for e in RS if e.get('type')=='novel']
AUT=[e for e in RS if e.get('type')=='author']
VOT=[e for e in RS if e.get('type')=='voter']

# 1 entity types
bad=[e.get('type') for e in RS if e.get('type') not in ('novel','author','voter')]
(ok if not bad else err)(f"rs/@type: {len(RS)} elements, only novel/author/voter" if not bad
   else f"rs/@type: unexpected values {set(bad)}")
ok(f"Distribution: {len(NOV)} novel, {len(AUT)} author, {len(VOT)} voter")

# 2 syntax of @ref
allref=[(e,e.get('ref')) for e in r.iter() if e.get('ref')]
wd=[(e,v) for e,v in allref if 'wikidata' in v]
badwd=[(e.tag.split('}')[1],v) for e,v in wd if not WDRX.match(v)]
other=[(e.tag.split('}')[1],v) for e,v in allref if 'wikidata' not in v]
(ok if not badwd else err)(f"@ref syntax: all {len(wd)} Wikidata references well formed"
   if not badwd else f"@ref syntax: malformed {badwd[:5]}")
badother=[(t,v) for t,v in other if not re.match(r'^https?://\S+$', v)]
(ok if not badother else err)(f"Other authority references: {len(other)} ({', '.join(sorted({t for t,_ in other}))}), all absolute URIs"
   if not badother else f"Malformed references: {badother}")

# 3 xml:id unique
ids=r.xpath('//@xml:id'); dup=[k for k,v in collections.Counter(ids).items() if v>1]
(ok if not dup else err)(f"xml:id: {len(ids)} values, all unique" if not dup else f"xml:id used twice: {dup}")

# 4 internal pointers
idset=set(ids); dangling=[]
for e in r.iter():
    for att in ('ana','next','prev','target','corresp'):
        v=e.get(att)
        if v:
            for tok in v.split():
                if tok.startswith('#') and tok[1:] not in idset: dangling.append((att,tok))
(ok if not dangling else err)("Internal pointers (@ana/@next/@prev/@target): all resolve"
   if not dangling else f"Dangling pointers: {sorted(set(dangling))}")

# 5 @ana discipline: works (#vote/#mention) and correspondents (one of the categories
# of taxonomy "correspondent-gender", read from the TEI header so that the script
# follows the vocabulary of the file: #female/#male/#unknown at the time of writing)
WORK_ANA={'#vote','#mention'}
GEND_ANA={'#'+c.get(XML+'id') for c in
          r.iterfind('.//t:taxonomy[@xml:id="correspondent-gender"]/t:category',
                     {**NS,'xml':'http://www.w3.org/XML/1998/namespace'})}
anas=[e for e in r.iter() if e.get('ana')]
wa=[e for e in anas if e.get('ana') in WORK_ANA]
ga=[e for e in anas if e.get('ana') in GEND_ANA]
badv=[e.get('ana') for e in anas if e.get('ana') not in WORK_ANA|GEND_ANA]
badt=([e.get('type') for e in wa if e.get('type')!='novel']
      +[e.get('type') for e in ga if e.get('type')!='voter'])
bads=[sect(e) for e in wa if sect(e)!='letters']
(ok if not (badv or badt or bads) else err)(
  f"@ana: {len(wa)}x on works ({sum(1 for e in wa if e.get('ana')=='#vote')} #vote, "
  f"{sum(1 for e in wa if e.get('ana')=='#mention')} #mention), only on rs/@type=novel inside "
  f"div[@type=letters]; {len(ga)}x on correspondents, only on rs/@type=voter"
  if not (badv or badt or bads) else f"@ana violated: values{set(badv)} types{set(badt)} sections{set(bads)}")

letnov=[e for e in r.find('.//t:div[@type="letters"]',NS).iter(T+'rs') if e.get('type')=='novel']
noana=[tx(e) for e in letnov if not e.get('ana')]
(ok if not noana else err)(f"Letters: all {len(letnov)} work references carry an @ana "
   f"({sum(1 for e in letnov if e.get('ana')=='#vote')} votes + {sum(1 for e in letnov if e.get('ana')=='#mention')} mentions)"
   if not noana else f"Without @ana: {noana[:8]}")

# 5a gender of the correspondents: complete, and drawn from the taxonomy
nogen=[tx(e.find(T+'persName')) for e in VOT if e.get('ana') not in GEND_ANA]
gdist=collections.Counter(e.get('ana','')[1:] for e in VOT if e.get('ana') in GEND_ANA)
(ok if not nogen else err)(
  f"Gender: all {len(VOT)} correspondents classified ("
  + ", ".join(f"{v}x {k}" for k,v in sorted(gdist.items(), key=lambda x:-x[1])) + ")"
  if not nogen else f"Without a gender value: {nogen[:8]}")

# 5b @cert
certs=[e for e in r.iter() if e.get('cert')]
badc=[e.get('cert') for e in certs if e.get('cert') not in ('high','medium','low','unknown')]
badct=[e.tag.split('}')[1] for e in certs if e.tag!=T+'rs']
noref=[tx(e) for e in certs if not e.get('ref')]
(ok if not (badc or badct) else err)(
  f"@cert: {len(certs)}x ({', '.join(f'{v} {k}' for k,v in sorted(collections.Counter(e.get('cert') for e in certs).items()))}), "
  f"only on rs, values conform to TEI"
  if not (badc or badct) else f"@cert violated: values{set(badc)} elements{set(badct)}")
(ok if not noref else warn)("@cert appears only on elements that carry an @ref"
  if not noref else f"@cert without @ref (meaningless): {noref}")
certgrp=collections.defaultdict(set)
for e in r.iter(T+'rs'):
    if e.get('ref'): certgrp[e.get('ref')].add(e.get('cert') or '')
split={q.rsplit('/',1)[1]:v for q,v in certgrp.items() if len(v)>1}
(ok if not split else warn)("@cert set consistently per entity"
  if not split else "Entity marked both with and without @cert: "+", ".join(sorted(split)))

# 6 taxonomy
# Categories are needed only for the @ana values; the @type values of <rs> are
# plain values and are explained in prose in the <encodingDesc>.
cats=set(r.xpath('//t:category/@xml:id',namespaces=NS))
used={a.get('ana','')[1:] for a in anas}-{''}
(ok if used<=cats else err)(f"Categories present for every @ana value: {sorted(used)}"
   if used<=cats else f"Missing categories: {sorted(used-cats)}")
unused=cats-used
if unused: warn(f"Category declared but never referenced: {sorted(unused)}")

# 6b authors: same spelling, different ids (ignoring @subtype=misattributed)
aform=collections.defaultdict(set)
for e in AUT:
    if e.get('subtype')=='misattributed': continue
    aform[norm(tx(e))].add(e.get('ref') or '')
amb={k:sorted(x.rsplit('/',1)[-1] for x in v) for k,v in aform.items() if len([x for x in v if x])>1}
(ok if not amb else warn)("Author spelling → id: unambiguous"
  if not amb else "Author name with more than one id (please check): "
    + "; ".join(f"{k}: {', '.join(v)}" for k,v in amb.items()))
sub=collections.Counter(e.get('subtype') for e in r.iter(T+'rs') if e.get('subtype'))
if sub: ok(f"@subtype: {dict(sub)}, only on rs")

# 7 spelling -> @ref (contradictions)
byform=collections.defaultdict(set)
for e in NOV: byform[norm(tx(e))].add(e.get('ref') or '')
conf={k:v for k,v in byform.items() if len([x for x in v if x])>1}
(ok if not conf else err)("Spelling → id: no contradictory assignments"
   if not conf else f"Contradiction: {conf}")
mixed={k:v for k,v in byform.items() if len(v)>1 and '' in v}
(ok if not mixed else warn)("Spelling → id: no spelling linked in one place and unlinked in another"
   if not mixed else "Linked in one place, unlinked in another: "+", ".join(sorted(mixed)))

# 8 @ref -> spellings
byref=collections.defaultdict(collections.Counter)
for e in NOV:
    if e.get('ref'): byref[e.get('ref')][tx(e)]+=1
multi={q:dict(c) for q,c in byref.items() if len(c)>1}
ok(f"Id → spellings: {len(byref)} works linked, {len(multi)} of them under more than one spelling")

# 9 the same id used for different entity types
tref=collections.defaultdict(set)
for e in RS:
    if e.get('ref'): tref[e.get('ref')].add(e.get('type'))
coll={q:v for q,v in tref.items() if len(v)>1}
(ok if not coll else err)("No id is used for two different entity types"
   if not coll else f"Id collision: {coll}")

# 10 page breaks
pbs=[p.get('n') for p in r.iter(T+'pb')]
(ok if pbs==[str(i) for i in range(1,24)] else err)(f"Page breaks: {len(pbs)} pb, 1-23 without a gap"
   if pbs==[str(i) for i in range(1,24)] else f"pb sequence: {pbs}")

# 11 letters
resp=r.findall('.//t:div[@type="response"]',NS)
nums=[d.get('n') for d in resp]
bad=[d.get('n') for d in resp if len([e for e in d.iter(T+'rs') if e.get('type')=='voter'])!=1]
(ok if not bad and nums==[str(i) for i in range(1,73)] else err)(
  f"Letters: {len(resp)} div[@type=response], n=1-72 without a gap, exactly one rs/@type=voter each"
  if not bad and nums==[str(i) for i in range(1,73)] else f"Faulty letters: {bad or nums}")
vids=[e.get(XML+'id') for e in VOT]
(ok if all(vids) and len(set(vids))==72 else err)("All 72 correspondents have a unique xml:id"
   if all(vids) and len(set(vids))==72 else "voter xml:id incomplete")
nopn=[e.get(XML+'id') for e in VOT if e.find('t:persName',NS) is None]
(ok if not nopn else warn)("Every voter contains a persName" if not nopn else f"Without persName: {nopn}")

# 12 votes per letter
per=[]
for d in resp:
    v=[e for e in d.iter(T+'rs') if e.get('type')=='novel' and e.get('ana')=='#vote']
    per.append((d.get('n'), tx(d.find('.//t:persName',NS)), len(v)))
odd=[x for x in per if x[2]!=10]
ok(f"Votes: {sum(x[2] for x in per)} in total; {len(per)-len(odd)} letters casting exactly ten")

# 13 works still without an id
gaps=collections.Counter(tx(e) for e in NOV if not e.get('ref'))
works=len({e.get('ref') or norm(tx(e)) for e in NOV})
linked=len(byref)
ok(f"Works: {works} distinct, {linked} with an id, {works-linked} without ({sum(gaps.values())} occurrences)")

# 14 comparison with the printed tally
printed={}
for it in r.iter(T+'item'):
    n=it.find('t:num',NS); q=it.find('t:rs',NS)
    if n is not None and q is not None:
        printed[q.get('ref') or norm(tx(q))]=(tx(q),int(tx(n)))
mine=collections.Counter()
for d in resp:
    for e in d.iter(T+'rs'):
        if e.get('type')=='novel' and e.get('ana')=='#vote':
            mine[e.get('ref') or norm(tx(e))]+=1
delta=[(lab,n,mine.get(k,0)) for k,(lab,n) in printed.items()]
exact=sum(1 for _,n,m in delta if n==m); over=[(l,n,m) for l,n,m in delta if m>n]
ok(f"Comparison with the printed tally: {exact} of {len(delta)} titles exact, "
   f"{len(over)} titles above the printed number")

print("="*100); print("CONSISTENCY CHECK:  Ten Great Novels, TEI P5"); print("="*100)
for m in OK:   print("  OK     ", m)
for m in WARN: print("  NOTE   ", m)
for m in ERR:  print("  ERROR  ", m)
print("\nLetters not casting exactly ten votes:")
for n,who,v in odd: print(f"   Letter {n:>2}  {who:<28} {v}")
if multi:
    print("\nWorks appearing under more than one spelling:")
    for q,c in sorted(multi.items(), key=lambda x:-sum(x[1].values())):
        print(f"   {q.rsplit('/',1)[1]:<12} " + " · ".join(f"{k} ({v})" for k,v in c.items()))
if over: print("\nAbove the printed number:", over)
print(f"\nRESULT: {len(ERR)} error{'' if len(ERR)==1 else 's'}, "
      f"{len(WARN)} note{'' if len(WARN)==1 else 's'}")
# Exit code for CI: 1 as soon as there is an error; notes have no effect.
sys.exit(1 if ERR else 0)
