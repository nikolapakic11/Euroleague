import json,re,unicodedata,collections,glob,math
T=json.load(open('/home/claude/live30/T.json'))
TG={'Valencia': 'BAR-PAM', 'Hapoel Tel-Aviv': 'DUB-HTA', 'Zalgiris Kaunas': 'ZAL-PAR', 'Dubai': 'DUB-HTA', 'Barcelona': 'BAR-PAM', 'Hapoel Tel Aviv': 'DUB-HTA', 'Virtus Bologna': 'VIR-BES', 'Panathinaikos': 'IST-PAN', 'Partizan': 'ZAL-PAR', 'Anadolu Efes': 'IST-PAN', 'Baskonia': 'ASV-BAS', 'Lyon-Villeurbanne': 'ASV-BAS', 'Besiktas': 'VIR-BES', 'Zalgiris': 'ZAL-PAR', 'Olympiacos': 'OLY-MIL', 'Olimpia Milano': 'OLY-MIL'}
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    x=unicodedata.normalize('NFD',x); x=''.join(c for c in x if unicodedata.category(c)!='Mn').lower().replace('đ','dj')
    x=re.sub(r"[.']",'',x); x=re.sub(r'-',' ',x); x=re.sub(r'[^a-z ]','',x); return ' '.join(w for w in x.split() if w not in SUF)
BOX={}; GINFO={}
for f in sorted(glob.glob('bs_*.json')):
    g=int(re.findall(r'\d+',f)[0])
    try: d=json.load(open(f))
    except Exception: continue
    bq=d.get('ByQuarter') or []; q=0
    for i in range(1,5):
        if any((r.get('Quarter%d'%i) or 0)>0 for r in bq): q=i
    sc=[(r['Team'], sum((r.get('Quarter%d'%i) or 0) for i in range(1,5))+sum((v or 0) for k,v in r.items() if k.startswith('Extra'))) for r in bq]
    GINFO[g]=dict(live=d.get('Live'),q=q,score=sc,mins=d.get('Minute'))
    for s in d.get('Stats',[]):
        for p in s['PlayersStats']:
            a=p['Player'].split(','); full=nk((a[1] if len(a)>1 else '')+' '+a[0])
            BOX[full]=dict(g=g,P=p['Points'],S=p['TotalRebounds'],A=p['Assistances'],min=p['Minutes'],pf=p.get('FoulsCommited'))
keys=list(BOX)
GC={'DUB-HTA':84,'ASV-BAS':85,'ZAL-PAR':86,'BAR-PAM':87,'IST-PAN':88,'VIR-BES':89,'OLY-MIL':90}
def find(name):
    k=nk(name)
    if k in BOX: return BOX[k]
    t=k.split(); c=[kk for kk in keys if kk.split()[-1]==t[-1] and kk.split()[0][:3]==t[0][:3]]
    if len(c)==1: return BOX[c[0]]
    return None
def finished(g):
    i=GINFO.get(g); return i and not i['live'] and i['q']>=4
def st(l):
    b=find(l['p'])
    if not b:
        g=GC.get(TG.get(l.get('team')))
        if g in GINFO and GINFO[g]['q']>=1: return ('void' if finished(g) else 'dnp',None,None)
        return ('pend',None,None)
    v=b[l['stat']]; dnp=b['min'] in ('DNP','',None,'00:00')
    if v>l['line']: return ('miss',v,b)
    if finished(b['g']): return ('void' if dnp else 'hit',v,b)
    return ('live',v,b)
for g,i in GINFO.items(): print('utakmica',g,i)
R=[]
for t in T:
    S_=[st(l) for l in t['legs']]; R.append((t,S_,sum(1 for s in S_ if s[0]=='miss')))
c=collections.Counter(min(m,2) for _,_,m in R); print('tiketa',len(R),'zivih',c[0],'jedan promasaj',c[1],'2+',c[2])
by=collections.defaultdict(lambda:[0,0,0])
for t,S_,m in R: by[(len(t['legs']),t['stake'])][min(m,2)]+=1
print('po vrsti [zivi, 1 promasaj, 2+]:',dict(by))
info={}; mc=collections.Counter(); cnt=collections.Counter()
for t,S_,m in R:
    for l,s in zip(t['legs'],S_):
        k=(l['p'],l['stat'],l['line']); info[k]=s; cnt[k]+=1
        if s[0]=='miss': mc[k]+=1
print('PROMASAJI:',[(k,v,info[k][1]) for k,v in mc.most_common()])
print('U TOKU / ZAVRSENO:')
for k,s in info.items():
    if s[0] in ('live','hit','void'):
        b=s[2]
        if b: print(f"  {s[0]:4s} {k[0]} {k[1]}<{k[2]}: {s[1]} ({b['min']} min, {b['pf']} f) na {cnt[k]} tiketa")
