# Kontekst za generator v6: pozicijska odbrana protivnika, ritam/poeni timova, uloga i forma igrača
import json,collections,statistics as stt,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','minusi'))
from putanje import BAZA
rows=json.load(open(BAZA+'/rows.json'))
OUT=sys.argv[1]
# 1) pozicijska odbrana: koliko protivnik dozvoljava bekovima/krilima/centrima po utakmici, u odnosu na ligu, skupljeno ka 1 (n/(n+6))
al=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda:[0,0,0])))
for r in rows:
    if r['pos'] not in ('G','F','C'): continue
    a=al[r['opp']][r['g']][r['pos']]; a[0]+=r['P']; a[1]+=r['S']; a[2]+=r['A']
lg={}
for pos in 'GFC':
    vals=[al[t][g][pos] for t in al for g in al[t]]
    lg[pos]=[stt.mean(v[i] for v in vals) for i in range(3)]
of={}
for t,gs in al.items():
    n=len(gs); of[t]={}
    for pos in 'GFC':
        of[t][pos]=[round(1+((stt.mean(gs[g][pos][i] for g in gs)/lg[pos][i])-1)*n/(n+6),3) for i in range(3)]
# 2) timovi: dati i primljeni poeni po utakmici
tg=collections.defaultdict(dict)
for r in rows:
    d=tg[r['team']].setdefault(r['g'],{'pts':0,'opp':r['opp']}); d['pts']+=r['P']
tm={}
for t,gs in tg.items():
    pf=[d['pts'] for d in gs.values()]; pa=[tg[d['opp']][g]['pts'] for g,d in gs.items() if g in tg[d['opp']]]
    tm[t]=[round(stt.mean(pf),1),round(stt.mean(pa),1),len(pf)]
lgp=round(stt.mean(v[0] for v in tm.values()),1)
# 3) igrači: pozicija, udeo startovanja, forma (učinak po minutu u poslednje 3 / cela sezona) za P,S,A
byk=collections.defaultdict(list)
for r in sorted(rows,key=lambda r:(r['d'],r['g'])):
    if r['min']>0: byk[r['k']].append(r)
pl={}
for k,g in byk.items():
    pos=collections.Counter(r['pos'] for r in g).most_common(1)[0][0]
    stv=round(sum(r['st'] for r in g)/len(g),2); m=sum(r['min'] for r in g); l3=g[-3:]; m3=sum(r['min'] for r in l3)
    fr=[]
    for s in 'PSA':
        rate=sum(r[s] for r in g)/m if m else 0; rate3=sum(r[s] for r in l3)/m3 if m3 else 0
        fr.append(round(rate3/rate,2) if rate>0 else 1)
    pl[k]=[pos if pos in 'GFC' else '',stv]+fr+[len(g)]
# 4) timski: koliko protivnici ukupno dobijaju P/S/A po utakmici, u odnosu na ligu (skupljeno n/(n+6))
og=collections.defaultdict(lambda: collections.defaultdict(lambda:[0,0,0]))
for r in rows:
    a=og[r['opp']][r['g']]; a[0]+=r['P']; a[1]+=r['S']; a[2]+=r['A']
lgt=[stt.mean(v[i] for t in og for v in og[t].values()) for i in range(3)]
ta={t:[round(1+((stt.mean(v[i] for v in gs.values())/lgt[i])-1)*len(gs)/(len(gs)+6),3) for i in range(3)] for t,gs in og.items()}
last=max(r['d'] for r in rows)[:10]
C2={'at':last,'src':'box score Evrolige, sve utakmice sezone 2026/27 do '+last,'lgp':lgp,'tm':tm,'of':of,'pl':pl,'ta':ta}
json.dump(C2,open(OUT,'w'),separators=(',',':'))
print('timova',len(tm),'igraca',len(pl),'lgp',lgp,'velicina',len(json.dumps(C2,separators=(',',':'))))
print('primer',list(pl.items())[:3]); print('ZAL',of.get('ZAL'),'PAM',tm.get('PAM'))
