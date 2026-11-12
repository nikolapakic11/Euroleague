import json,sys,collections,math,statistics as st,glob,re,os
R='/home/claude/Euroleague'; os.chdir(R); sys.path.insert(0,R+'/spoj')
import signali
S=signali.Signali(); B=S.B
D=json.load(open('spoj/provera/skup.json'))
G=json.load(open('baza/games.json'))['data']
home={}
for g in G: home[(g['date'][:10],g['local']['club']['code'])]=1; home[(g['date'][:10],g['road']['club']['code'])]=0
rows=B.rows
byteam=collections.defaultdict(lambda: collections.defaultdict(list))   # team -> dan -> rows
for r in rows: byteam[r['team']][r['dan']].append(r)
def team_pre(team,dan):
    ds=sorted(d for d in byteam[team] if d<dan); return ds
tg=collections.defaultdict(dict)
for r in rows: tg[r['team']].setdefault(r['dan'],{'pts':0,'opp':r['opp']}); tg[r['team']][r['dan']]['pts']+=r['P']
def margin(team,dan):
    v=[tg[team][d]['pts']-tg[tg[team][d]['opp']][d]['pts'] for d in tg[team] if d<dan and d in tg[tg[team][d]['opp']]]
    return sum(v)/len(v) if v else 0
from datetime import date
def dd(a,b): return (date.fromisoformat(a)-date.fromisoformat(b)).days
cons=collections.defaultdict(list)
for x in D: cons[(x['dan'],x['k'],x['s'])].append(x)
out=[]
for x in D:
    k=x['k']; dan=x['dan']; s=x['s']
    g=[r for r in B.byk[k] if r['dan']<dan and r['min']>0]
    td=[r for r in B.byk[k] if r['dan']==dan][0]; team=td['team']; opp=td['opp']
    n=len(g)
    if n<2: continue
    v=[r[s] for r in g]; avg=sum(v)/n; sd=st.pstdev(v) if n>2 else max(1,avg**.5)
    mn=[r['min'] for r in g]; am=sum(mn)/n
    l3=g[-3:]; a3=sum(r[s] for r in l3)/len(l3); m3=sum(r['min'] for r in l3)/len(l3)
    f=dict(x); f['y']=1-x['preko']; f['opp']=opp; f['team']=team; f['act']=td[s]; f['actmin']=td['min']
    f['dom']=home.get((dan,team)); f['n']=n; f['avg']=avg; f['zline']=(x['l']-avg)/max(sd,0.8); f['hot']=(a3-avg)/max(sd,0.8); f['mintrend']=m3-am; f['am']=am
    f['emp']=(sum(1 for t in v if t<x['l'])+1)/(n+2); f['st']=sum(r['st'] for r in g)/n; f['pos']=td['pos']
    f['mdiff']=margin(team,dan)-margin(opp,dan)
    pd=team_pre(team,dan); f['rest']=dd(dan,pd[-1]) if pd else 9
    # rotacija tima pre dana: prosečni minuti po igraču
    pre=collections.defaultdict(list)
    for d0 in pd:
        for r in byteam[team][d0]:
            if r['min']>0: pre[r['k']].append(r['min'])
    rot={p:sum(m)/len(m) for p,m in pre.items() if len(m)>=3 and sum(m)/len(m)>=10}
    today={r['k'] for r in byteam[team][dan] if r['min']>0}
    last={r['k'] for r in byteam[team][pd[-1]] if r['min']>0} if pd else set()
    f['missmin']=sum(m for p,m in rot.items() if p not in today and p!=k)
    f['retmin']=sum(m for p,m in rot.items() if p in today and p not in last and p!=k)
    # rang u timu po proseku stavke
    tavg={}
    for d0 in pd:
        for r in byteam[team][d0]:
            if r['min']>0: tavg.setdefault(r['k'],[]).append(r[s])
    rk=sorted(((sum(a)/len(a)) for p,a in tavg.items() if len(a)>=3),reverse=True)
    f['rang']=1+sum(1 for a in rk if a>avg)
    C=cons[(dan,k,s)]; ls=sorted({c['l'] for c in C}); bk={c['izvor'] for c in C}
    f['nbk']=len(bk); f['ldev']=x['l']-st.median([c['l'] for c in C]) if len(bk)>=2 else None
    out.append(f)
json.dump(out,open('spoj/analiza/F.json','w')); print('F',len(out), collections.Counter(x['izvor'] for x in out))
# kretanje granica iz sirovih ponuda
def dan_iz(t):
    m=re.search(r'(\d+)\.\s*(\d+)\.\s*(\d{4})',t or ''); return f"{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}" if m else None
mv=[]
for bkdir in glob.glob('baza/ponude/*'):
    bkn=os.path.basename(bkdir); files=collections.defaultdict(list)
    for fn in sorted(glob.glob(bkdir+'/*.json')):
        try: d=json.load(open(fn))
        except Exception: continue
        P=d.get('picks') or []
        byd=collections.defaultdict(dict)
        for p in P:
            dn=dan_iz(p.get('time')) or os.path.basename(fn)[:10]
            if p.get('u') is None or p.get('o') is None or p.get('s') not in ('P','S','A'): continue
            key=(p['p'],p.get('t'),p['s']); cur=byd[dn].get(key)
            if cur is None or abs(1/p['u']-1/p['o'])<abs(1/cur['u']-1/cur['o']): byd[dn][key]=p
        for dn,m in byd.items(): files[dn].append((d.get('at') or fn,m))
    for dn,L in files.items():
        if len(L)<2: continue
        L.sort(key=lambda t:t[0]); a,b=L[0][1],L[-1][1]
        for key in set(a)&set(b):
            pa,pb=a[key],b[key]
            k,_=S.nadji(key[0],key[1],None)
            if not k: continue
            r=[r for r in B.byk.get(k,[]) if r['dan']==dn and r['min']>0]
            if not r: continue
            fa=(1/pa['o'])/(1/pa['u']+1/pa['o']); fb=(1/pb['o'])/(1/pb['u']+1/pb['o'])
            mv.append(dict(bk=bkn,dan=dn,k=k,s=key[2],l0=pa['l'],l1=pb['l'],u0=pa['u'],o0=pa['o'],u1=pb['u'],o1=pb['o'],f0=fa,f1=fb,act=r[0][key[2]]))
json.dump(mv,open('spoj/analiza/MV.json','w')); print('kretanja',len(mv),collections.Counter(x['bk'] for x in mv))
