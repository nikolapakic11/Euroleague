import json, math, random, collections, time, sys
import numpy as np
from statistics import NormalDist
ND=NormalDist()
cfg=json.loads(sys.argv[1])
rows=json.load(open(cfg.get('rows','scored.json')))
excl=set(cfg.get('excl',[])); caps=cfg.get('caps',{})
best={}
for r in rows:
    if r['p'] in excl: continue
    if r['p'] not in best: best[r['p']]=r
ALL=sorted(best.values(),key=lambda r:-r['pr'])
N=cfg['N']; L=cfg['L']; FIRST=set(cfg['first']); NF=cfg['nf']; gcap=cfg['gcap']; tiers=cfg['tiers']
P=[]; cnt=[]; total=0; fs=0; gsl=collections.Counter(); GMAX=cfg.get('gmax',N*2)
for r in ALL:
    if total>=N*L: break
    rank=len(P)
    c=next((c for lim,c in tiers if rank<lim), tiers[-1][1])
    c=min(c, caps.get(r['p'],99))
    if r['g'] in FIRST:
        c=min(c, NF*3-fs)
        if c<=0: continue
        fs+=c
    c=min(c,N*L-total, GMAX-gsl[r['g']])
    if c<=0: continue
    gsl[r['g']]+=c
    P.append(r); cnt.append(c); total+=c
print('slots per game', dict(gsl)); assert total==N*L, total
fz=[i for i,r in enumerate(P) if r['g'] in FIRST]; ot=[i for i in range(len(P)) if i not in fz]
def legal(t,i):
    if any(P[j]['p']==P[i]['p'] for j in t): return False
    if sum(1 for j in t if P[j]['t']==P[i]['t'])>=3: return False
    if sum(1 for j in t if P[j]['g']==P[i]['g'])>=gcap: return False
    return True
def construct(sd):
    R=random.Random(sd); tk=[[] for _ in range(N)]
    a=[i for i in fz for _ in range(cnt[i])]; b=[i for i in ot for _ in range(cnt[i])]; R.shuffle(a); R.shuffle(b)
    for i in sorted(a,key=lambda i:-cnt[i]):
        c=[k for k in range(NF) if len(tk[k])<L and legal(tk[k],i)]
        if not c: return None
        k=min(c,key=lambda k:len(tk[k])+R.random()); tk[k].append(i)
    for i in sorted(b,key=lambda i:-cnt[i]):
        c=[k for k in range(N) if len(tk[k])<L and legal(tk[k],i)]
        if not c: return None
        k=min(c,key=lambda k:len(tk[k])+R.random()); tk[k].append(i)
    return tk if all(len(t)==L for t in tk) else None
tk=None
for sd in range(400):
    tk=construct(cfg.get('seed',1)*1000+sd)
    if tk: break
assert tk, 'no construct'
teams=sorted({r['t'] for r in P}); ti={t:i for i,t in enumerate(teams)}
def scen(key,M,s,rho=0.06):
    rng=np.random.default_rng(s); Z=rng.standard_normal((len(teams),M)); H=np.zeros((len(P),M),bool)
    for i,r in enumerate(P):
        p=min(0.88,max(0.1,r[key])); y=math.sqrt(rho)*Z[ti[r['t']]]+math.sqrt(1-rho)*rng.standard_normal(M); H[i]=y<ND.inv_cdf(p)
    return H
Ht=scen('pr',6000,1); R=random.Random(7)
hv=[np.all(Ht[t],axis=0) for t in tk]; cw=np.sum(hv,axis=0); cur=(cw>0).mean(); t0=time.time()
while time.time()-t0<cfg.get('secs',60):
    a=R.randrange(N); b=R.randrange(N)
    if a==b: continue
    i=R.randrange(L); j=R.randrange(L); x=tk[a][i]; y=tk[b][j]
    if (P[x]['g'] in FIRST and b>=NF) or (P[y]['g'] in FIRST and a>=NF): continue
    ta=tk[a][:i]+tk[a][i+1:]; tb=tk[b][:j]+tk[b][j+1:]
    if not (legal(ta,y) and legal(tb,x)): continue
    ta.append(y); tb.append(x); ha=np.all(Ht[ta],axis=0); hb=np.all(Ht[tb],axis=0)
    nc=cw-hv[a]-hv[b]+ha+hb; nv=(nc>0).mean()
    if nv>=cur: tk[a],tk[b]=ta,tb; hv[a],hv[b]=ha,hb; cw=nc; cur=nv
def ev(key):
    H=scen(key,100000,9); M=H.shape[1]; w=np.zeros(M); ref=np.zeros(M)
    for t in tk:
        h=H[t].sum(axis=0); w+=h==L; ref+=h==L-1
    return round(float((w>=1).mean()),3), round(float(w.mean()),2), round(float(ref.mean()),2)
pc=collections.Counter(P[i]['p'] for t in tk for i in t)
gc=collections.Counter(g for t in tk for g in {P[i]['g'] for i in t})
odds=[math.prod(P[i]['u'] for i in t) for t in tk]
st=cfg['stake']; bo=cfg['bonus']
print('pairs', len(pc), 'max', max(pc.values()), dict(gc))
print('est', ev('pr'), 'market', ev('fair'), 'odds', round(min(odds)), round(max(odds)), 'win', round(min(odds)*st*(1+bo)), round(max(odds)*st*(1+bo)))
print(sorted(((P[i]['p'],P[i]['s'],P[i]['l'],P[i]['u']) for i in range(len(P))), key=lambda x:-pc[x[0]])[:0])
print([(k,v) for k,v in pc.most_common()])
out={'v':1,'round':cfg['round'],'tickets':[{'stake':st,'legs':[{'c':P[i]['c'],'p':P[i]['p'],'t':P[i]['t'],'s':P[i]['s'],'l':P[i]['l'],'u':P[i]['u']} for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['p']))]} for t in tk]}
json.dump(out,open(cfg['out'],'w'),ensure_ascii=False,separators=(',',':'))
