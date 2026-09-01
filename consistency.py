# -*- coding: utf-8 -*-
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

# 1 Typen
bad=[e.get('type') for e in RS if e.get('type') not in ('novel','author','voter')]
(ok if not bad else err)(f"rs/@type: {len(RS)} Elemente, nur novel/author/voter" if not bad
   else f"rs/@type: unerwartete Werte {set(bad)}")
ok(f"Verteilung: {len(NOV)} novel, {len(AUT)} author, {len(VOT)} voter")

# 2 ref-Syntax
allref=[(e,e.get('ref')) for e in r.iter() if e.get('ref')]
wd=[(e,v) for e,v in allref if 'wikidata' in v]
badwd=[(e.tag.split('}')[1],v) for e,v in wd if not WDRX.match(v)]
other=[(e.tag.split('}')[1],v) for e,v in allref if 'wikidata' not in v]
(ok if not badwd else err)(f"@ref-Syntax: alle {len(wd)} Wikidata-Verweise korrekt geformt"
   if not badwd else f"@ref-Syntax: ungültig {badwd[:5]}")
badother=[(t,v) for t,v in other if not re.match(r'^https?://\S+$', v)]
(ok if not badother else err)(f"Weitere Normdaten-Verweise: {len(other)} ({', '.join(sorted({t for t,_ in other}))}), alle absolute URIs"
   if not badother else f"ungültige Verweise: {badother}")

# 3 xml:id eindeutig
ids=r.xpath('//@xml:id'); dup=[k for k,v in collections.Counter(ids).items() if v>1]
(ok if not dup else err)(f"xml:id: {len(ids)} Werte, alle eindeutig" if not dup else f"xml:id doppelt: {dup}")

# 4 interne Zeiger
idset=set(ids); dangling=[]
for e in r.iter():
    for att in ('ana','next','prev','target','corresp'):
        v=e.get(att)
        if v:
            for tok in v.split():
                if tok.startswith('#') and tok[1:] not in idset: dangling.append((att,tok))
(ok if not dangling else err)("Interne Zeiger (@ana/@next/@prev/@target): alle auflösbar"
   if not dangling else f"tote Zeiger: {sorted(set(dangling))}")

# 5 ana-Disziplin
anas=[e for e in r.iter() if e.get('ana')]
badv=[e.get('ana') for e in anas if e.get('ana') not in ('#vote','#mention')]
badt=[e.get('type') for e in anas if e.get('type')!='novel']
bads=[sect(e) for e in anas if sect(e)!='letters']
(ok if not (badv or badt or bads) else err)(
  f"@ana: {len(anas)}x ({sum(1 for e in anas if e.get('ana')=='#vote')} #vote, "
  f"{sum(1 for e in anas if e.get('ana')=='#mention')} #mention), nur auf rs/@type=novel, nur in div[@type=letters]"
  if not (badv or badt or bads) else f"@ana verletzt: Werte{set(badv)} Typen{set(badt)} Sektionen{set(bads)}")

letnov=[e for e in r.find('.//t:div[@type="letters"]',NS).iter(T+'rs') if e.get('type')=='novel']
noana=[tx(e) for e in letnov if not e.get('ana')]
(ok if not noana else err)(f"Briefsektion: alle {len(letnov)} Werknennungen tragen ein @ana "
   f"({sum(1 for e in letnov if e.get('ana')=='#vote')} Stimmen + {sum(1 for e in letnov if e.get('ana')=='#mention')} Erwähnungen)"
   if not noana else f"ohne @ana: {noana[:8]}")

# 5b @cert
certs=[e for e in r.iter() if e.get('cert')]
badc=[e.get('cert') for e in certs if e.get('cert') not in ('high','medium','low','unknown')]
badct=[e.tag.split('}')[1] for e in certs if e.tag!=T+'rs']
noref=[tx(e) for e in certs if not e.get('ref')]
(ok if not (badc or badct) else err)(
  f"@cert: {len(certs)}x ({', '.join(f'{v} {k}' for k,v in sorted(collections.Counter(e.get('cert') for e in certs).items()))}), "
  f"nur auf rs, TEI-konforme Werte"
  if not (badc or badct) else f"@cert verletzt: Werte{set(badc)} Elemente{set(badct)}")
(ok if not noref else warn)("@cert steht durchweg auf Elementen mit @ref"
  if not noref else f"@cert ohne @ref (sinnlos): {noref}")
certgrp=collections.defaultdict(set)
for e in r.iter(T+'rs'):
    if e.get('ref'): certgrp[e.get('ref')].add(e.get('cert') or '')
split={q.rsplit('/',1)[1]:v for q,v in certgrp.items() if len(v)>1}
(ok if not split else warn)("@cert je Entität einheitlich gesetzt"
  if not split else "Entität mit und ohne @cert ausgezeichnet: "+", ".join(sorted(split)))

# 6 Taxonomie
# Kategorien muss es nur fuer die @ana-Werte geben; die @type-Werte von <rs>
# sind einfache Werte und werden im <encodingDesc> in Prosa erklaert.
cats=set(r.xpath('//t:category/@xml:id',namespaces=NS))
used={a.get('ana','')[1:] for a in anas}-{''}
(ok if used<=cats else err)(f"Kategorien fuer alle @ana-Werte vorhanden: {sorted(used)}"
   if used<=cats else f"fehlende Kategorien: {sorted(used-cats)}")
unused=cats-used
if unused: warn(f"Kategorie(n) deklariert, aber nie referenziert: {sorted(unused)}")

# 6b Autoren: gleiche Schreibung, verschiedene IDs (ohne @subtype=misattributed)
AUT=[e for e in r.iter(T+'rs') if e.get('type')=='author']
aform=collections.defaultdict(set)
for e in AUT:
    if e.get('subtype')=='misattributed': continue
    aform[norm(tx(e))].add(e.get('ref') or '')
amb={k:sorted(x.rsplit('/',1)[-1] for x in v) for k,v in aform.items() if len([x for x in v if x])>1}
(ok if not amb else warn)("Autorenschreibung→ID: eindeutig"
  if not amb else "Autorenname mit mehreren IDs (pruefen): "
    + "; ".join(f"{k}: {', '.join(v)}" for k,v in amb.items()))
sub=collections.Counter(e.get('subtype') for e in r.iter(T+'rs') if e.get('subtype'))
if sub: ok(f"@subtype: {dict(sub)}, nur auf rs")

# 7 Schreibung -> ref  (Widerspruchsprüfung)
byform=collections.defaultdict(set)
for e in NOV: byform[norm(tx(e))].add(e.get('ref') or '')
conf={k:v for k,v in byform.items() if len([x for x in v if x])>1}
(ok if not conf else err)("Schreibung→ID: keine widersprüchlichen Zuordnungen"
   if not conf else f"Widerspruch: {conf}")
mixed={k:v for k,v in byform.items() if len(v)>1 and '' in v}
(ok if not mixed else warn)("Schreibung→ID: keine Form teils verknüpft, teils nicht"
   if not mixed else "teils verknüpft, teils nicht: "+", ".join(sorted(mixed)))

# 8 ref -> Schreibungen
byref=collections.defaultdict(collections.Counter)
for e in NOV:
    if e.get('ref'): byref[e.get('ref')][tx(e)]+=1
multi={q:dict(c) for q,c in byref.items() if len(c)>1}
ok(f"ID→Schreibungen: {len(byref)} Werke verknüpft, davon {len(multi)} mit mehreren Schreibungen")

# 9 ref-Kollision zwischen Typen
tref=collections.defaultdict(set)
for e in RS:
    if e.get('ref'): tref[e.get('ref')].add(e.get('type'))
coll={q:v for q,v in tref.items() if len(v)>1}
(ok if not coll else err)("Keine ID wird für zwei verschiedene Entitätstypen benutzt"
   if not coll else f"ID-Kollision: {coll}")

# 10 pb
pbs=[p.get('n') for p in r.iter(T+'pb')]
(ok if pbs==[str(i) for i in range(1,24)] else err)(f"Seitenwechsel: {len(pbs)} pb, lückenlos 1–23"
   if pbs==[str(i) for i in range(1,24)] else f"pb-Folge: {pbs}")

# 11 Briefe
resp=r.findall('.//t:div[@type="response"]',NS)
nums=[d.get('n') for d in resp]
bad=[d.get('n') for d in resp if len([e for e in d.iter(T+'rs') if e.get('type')=='voter'])!=1]
(ok if not bad and nums==[str(i) for i in range(1,73)] else err)(
  f"Briefe: {len(resp)} div[@type=response], n=1–72 lückenlos, je genau ein rs/@type=voter"
  if not bad and nums==[str(i) for i in range(1,73)] else f"Briefe fehlerhaft: {bad or nums}")
vids=[e.get(XML+'id') for e in VOT]
(ok if all(vids) and len(set(vids))==72 else err)("Alle 72 Briefschreiber haben eine eindeutige xml:id"
   if all(vids) and len(set(vids))==72 else "voter-xml:id unvollständig")
nopn=[e.get(XML+'id') for e in VOT if e.find('t:persName',NS) is None]
(ok if not nopn else warn)("Jeder voter enthält einen persName" if not nopn else f"ohne persName: {nopn}")

# 12 Stimmen je Brief
per=[]
for d in resp:
    v=[e for e in d.iter(T+'rs') if e.get('type')=='novel' and e.get('ana')=='#vote']
    per.append((d.get('n'), tx(d.find('.//t:persName',NS)), len(v)))
odd=[x for x in per if x[2]!=10]
ok(f"Stimmen: {sum(x[2] for x in per)} insgesamt; {len(per)-len(odd)} Briefe mit genau zehn")

# 13 Lücken
gaps=collections.Counter(tx(e) for e in NOV if not e.get('ref'))
works=len({e.get('ref') or norm(tx(e)) for e in NOV})
linked=len(byref)
ok(f"Werke: {works} verschieden, {linked} mit ID, {works-linked} ohne ({sum(gaps.values())} Belege)")

# 14 Abgleich mit der gedruckten Auszählung
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
ok(f"Abgleich mit gedruckter Auszählung: {exact} von {len(delta)} Titeln exakt, "
   f"{len(over)} Titel über der gedruckten Zahl")

print("="*100); print("KONSISTENZTEST  —  Ten Great Novels, TEI P5"); print("="*100)
for m in OK:   print("  OK    ", m)
for m in WARN: print("  HINWEIS", m)
for m in ERR:  print("  FEHLER ", m)
print("\nStimmen abweichend von zehn:")
for n,who,v in odd: print(f"   Brief {n:>2}  {who:<28} {v}")
if multi:
    print("\nWerke mit mehreren Schreibungen im Band:")
    for q,c in sorted(multi.items(), key=lambda x:-sum(x[1].values())):
        print(f"   {q.rsplit('/',1)[1]:<12} " + " · ".join(f"{k} ({v})" for k,v in c.items()))
if over: print("\nÜber gedruckter Zahl:", over)
print(f"\nERGEBNIS: {len(ERR)} Fehler, {len(WARN)} Hinweise")
# Exit-Code fuer CI: 1, sobald ein Fehler vorliegt (Hinweise bleiben folgenlos)
import sys as _sys
_sys.exit(1 if ERR else 0)
