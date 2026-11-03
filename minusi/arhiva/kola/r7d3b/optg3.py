import json,math,random,collections,time,sys
import numpy as np
from statistics import NormalDist
ND=NormalDist()
CFG=json.loads(sys.argv[1]); P=json.load(open(CFG['sel'])); n=len(P)
SIZES=CFG['sizes']; N=len(SIZES); S=sum(SIZES)
GCS={int(k):v for k,v in CFG['gcaps'].items()}; TCAP=CFG.get('tcap',3)
MAXU=CFG['maxu']; MINU=CFG['minu']; PMAX=CFG['pmax']; K=CFG.get('k',10); SEED=CFG.get('seed',1); SECS=CFG.get('secs',60)
R=random.Random(SEED)
pm=np.mean([x['pr'] for x in P]); w=np.array([math.exp(K*(x['pr']-pm)) for x in P])
players=sorted({x['p'] for x in P}); pid=[players.index(x['p']) for x in P]
# capacity per game/team over all tickets
gcapT=collections.Counter(); 
for L in SIZES:
    for g,c in GCS[L].items(): gcapT[g]+=c
teams=sorted({x['t'] for x in P}); tcapT={t:TCAP*N for t in teams}
cnt=np.clip(np.round(S*w/w.sum()),MINU,MAXU).astype(int)
def grp(key):
    d=collections.defaultdict(list)
    for i,x in enumerate(P): d[x[key]].append(i)
    return d
GG=grp('g'); TT=grp('t'); PP=collections.defaultdict(list)
for i in range(n): PP[pid[i]].append(i)
def over():
    for g,ids in GG.items():
        if cnt[ids].sum()>gcapT[g]: return ids
    for t,ids in TT.items():
        if cnt[ids].sum()>tcapT[t]: return ids
    for p,ids in PP.items():
        if cnt[ids].sum()>PMAX: return ids
    return None
def room(i):
    if cnt[i]>=MAXU: return False
    if cnt[GG[P[i]['g']]].sum()>=gcapT[P[i]['g']]: return False
    if cnt[TT[P[i]['t']]].sum()>=tcapT[P[i]['t']]: return False
    if cnt[PP[pid[i]]].sum()>=PMAX: return False
    return True
for _ in range(5000):
    ids=over()
    if ids is not None:
        j=max(ids,key=lambda i:cnt[i]/w[i]);
        if cnt[j]>0: cnt[j]-=1
        continue
    d=S-cnt.sum()
    if d==0: break
    if d>0:
        c=[i for i in range(n) if room(i)]
        if not c: raise SystemExit('cannot place, increase caps')
        i=max(c,key=lambda i:w[i]/(cnt[i]+1)); cnt[i]+=1
    else:
        i=max(range(n),key=lambda i:cnt[i]/w[i]); cnt[i]-=1
assert cnt.sum()==S
pc=collections.Counter(); 
for i in range(n): pc[P[i]['p']]+=cnt[i]
print('player use',sorted(pc.items(),key=lambda x:-x[1]))
def legal(t,i,L):
    if any(pid[j]==pid[i] for j in t): return False
    if sum(1 for j in t if P[j]['t']==P[i]['t'])>=TCAP: return False
    if sum(1 for j in t if P[j]['g']==P[i]['g'])>=GCS[L].get(P[i]['g'],0): return False
    return True
def construct(sd):
    Rr=random.Random(sd); tk=[[] for _ in range(N)]; left=cnt.copy()
    order=sorted(range(N),key=lambda k:-SIZES[k]); 
    for idx,k in enumerate(order):
        remT=N-idx
        for _ in range(SIZES[k]):
            c=[i for i in range(n) if left[i]>0 and legal(tk[k],i,SIZES[k])]
            if not c: return None
            i=max(c,key=lambda i:left[i]/remT+Rr.random()*0.3); tk[k].append(i); left[i]-=1
    return tk
tk=None
for sd in range(3000):
    tk=construct(SEED*10000+sd)
    if tk: break
assert tk,'no construct'
teamsL=sorted({x['t'] for x in P}); ti={t:i for i,t in enumerate(teamsL)}
gamesL=sorted({x['g'] for x in P}); gi={g:i for i,g in enumerate(gamesL)}
playersL=players
def scen(key,M,s,rho=0.06,rg=0.04,rp=0.35):
    rng=np.random.default_rng(s); Z=rng.standard_normal((len(teamsL),M)); G=rng.standard_normal((len(gamesL),M)); PL=rng.standard_normal((len(playersL),M)); H=np.zeros((n,M),bool)
    for i,x in enumerate(P):
        p=x[key]; y=math.sqrt(rho)*Z[ti[x['t']]]+math.sqrt(rg)*G[gi[x['g']]]+math.sqrt(rp)*PL[pid[i]]+math.sqrt(1-rho-rg-rp)*rng.standard_normal(M); H[i]=y<ND.inv_cdf(p)
    return H
M=30000; Ht=scen('pr',M,SEED+100)
hv=[np.all(Ht[t],axis=0) for t in tk]; cw=np.sum(hv,axis=0)
def J(cw): return cw.mean()+(cw>0).mean()
cur=J(cw); t0=time.time(); it=0
sig=lambda t:tuple(sorted(t))
while time.time()-t0<SECS:
    it+=1
    a=R.randrange(N); b=R.randrange(N)
    if a==b: continue
    i=R.randrange(SIZES[a]); j=R.randrange(SIZES[b]); x=tk[a][i]; y=tk[b][j]
    if x==y: continue
    ta=tk[a][:i]+tk[a][i+1:]; tb=tk[b][:j]+tk[b][j+1:]
    if not (legal(ta,y,SIZES[a]) and legal(tb,x,SIZES[b])): continue
    ta.append(y); tb.append(x)
    sa,sb=sig(ta),sig(tb)
    if sa==sb or any(sig(t)==sa or sig(t)==sb for k,t in enumerate(tk) if k not in (a,b)): continue
    ha=np.all(Ht[ta],axis=0); hb=np.all(Ht[tb],axis=0)
    nc=cw-hv[a]-hv[b]+ha+hb; nv=J(nc)
    if nv>=cur: tk[a],tk[b]=ta,tb; hv[a],hv[b]=ha,hb; cw=nc; cur=nv
def ev(key,s=9,M=200000):
    H=scen(key,M,s); w=np.zeros(M); ref=np.zeros(M); bys=collections.defaultdict(float)
    for k,t in enumerate(tk):
        hh=H[t].sum(axis=0); win=hh==len(t); w+=win; ref+=hh==len(t)-1; bys[len(t)]+=win.mean()
    return dict(p1=round(float((w>=1).mean()),3), ew=round(float(w.mean()),3), bys={k:round(v,3) for k,v in bys.items()}, ref=round(float(ref.mean()),2))
print('iters',it,'est',ev('pr'),'market',ev('fair'))
uc=collections.Counter(P[i]['p'] for t in tk for i in t); print('player tickets',sorted(uc.items(),key=lambda x:-x[1]))
pc2=collections.Counter(i for t in tk for i in t); print('max pair',max(pc2.values()))
ov=[len({pid[i] for i in a}&{pid[i] for i in b})/min(len(a),len(b)) for x,a in enumerate(tk) for b in tk[x+1:]]
print('avg shared players share',round(sum(ov)/len(ov),3))
json.dump({'tk':tk},open(CFG['out'],'w'))
