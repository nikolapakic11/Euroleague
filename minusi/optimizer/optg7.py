import json,math,random,collections,time,sys
import numpy as np
from statistics import NormalDist
ND=NormalDist()
CFG=json.loads(sys.argv[1]); P=json.load(open(CFG['sel'])); n=len(P)
SIZES=CFG['sizes']; N=len(SIZES)
GCS={int(k):v for k,v in CFG['gcaps'].items()}; TCAP=CFG.get('tcap',3)
MAXU=CFG['maxu']; PMAX=CFG['pmax']; K=CFG.get('k',10); SEED=CFG.get('seed',1); SECS=CFG.get('secs',60)
R=random.Random(SEED)
FIX=CFG.get('fixed',[]); NF=len(FIX); LOCK=set(CFG.get('lock',[])); LOWU=CFG.get('lowu',0); LOWMAX=CFG.get('lowmax',99); OTH=CFG.get('lowothers',0)
pm=np.mean([x['pr'] for x in P]); w=[math.exp(K*(x['pr']-pm)) for x in P]
players=sorted({x['p'] for x in P}); pid=[players.index(x['p']) for x in P]
use=[0]*n; puse=[0]*len(players)
def legal(t,i,L,skip=-1):
    if i in LOCK: return False
    if puse[pid[i]]-pfix[pid[i]]>=PNEW: return False
    if OTH:  # ako je u tiketu kvota ispod LOWU, sve ostale moraju biti >= OTH
        ot=[P[j]['u'] for k,j in enumerate(t) if k!=skip]
        if P[i]['u']<LOWU and any(u<OTH for u in ot): return False
        if P[i]['u']<OTH and any(u<LOWU for u in ot): return False
    if P[i]['u']<LOWU and sum(1 for k,j in enumerate(t) if k!=skip and P[j]['u']<LOWU)>=LOWMAX: return False
    if use[i]>=MAXU or puse[pid[i]]>=PMAX: return False
    tc=gc=0
    for k,j in enumerate(t):
        if k==skip: continue
        if pid[j]==pid[i]: return False
        if P[j]['t']==P[i]['t']: tc+=1
        if P[j]['g']==P[i]['g']: gc+=1
    return tc<TCAP and gc<GCS[L].get(P[i]['g'],0)
def add(i,d): use[i]+=d; puse[pid[i]]+=d
tk=[None]*N
for k,t in enumerate(FIX):
    tk[k]=list(t)
    for i in t: add(i,1)
pfix=puse[:]; PNEW=CFG.get('pnew',10**6)
order=sorted(range(NF,N),key=lambda k:-SIZES[k])
for k in order:
    L=SIZES[k]
    for att in range(3000):
        t=[]
        for _ in range(L):
            c=[i for i in range(n) if legal(t,i,L)]
            if not c: break
            ws=[w[i]**0.5*((MAXU-use[i])/MAXU)*((PMAX-puse[pid[i]])/PMAX)**3 for i in c]
            r=R.random()*sum(ws); pick=c[-1]
            for i,x in zip(c,ws):
                r-=x
                if r<=0: pick=i; break
            t.append(pick); add(pick,1)
        if len(t)==L: tk[k]=t; break
        for i in t: add(i,-1)
    if tk[k] is None:
        print('FAIL at ticket',order.index(k),'size',L)
        rem=collections.Counter(); 
        for i in range(n): rem[(P[i]['g'],P[i]['p'])]=max(rem[(P[i]['g'],P[i]['p'])],0)
        byp={}
        for i in range(n):
            if use[i]<MAXU: byp[P[i]['p']]=(P[i]['g'],PMAX-puse[pid[i]])
        print(sorted(byp.items(),key=lambda x:x[1]))
        sys.exit(1)
teamsL=sorted({x['t'] for x in P}); ti={t:i for i,t in enumerate(teamsL)}
gamesL=sorted({x['g'] for x in P}); gi={g:i for i,g in enumerate(gamesL)}
def scen(key,M,s,rho=0.02,rg=0.02,rp=0.35):
    rng=np.random.default_rng(s); Z=rng.standard_normal((len(teamsL),M)); G=rng.standard_normal((len(gamesL),M)); PL=rng.standard_normal((len(players),M)); H=np.zeros((n,M),bool)
    for i,x in enumerate(P):
        y=math.sqrt(rho)*Z[ti[x['t']]]+math.sqrt(rg)*G[gi[x['g']]]+math.sqrt(rp)*PL[pid[i]]+math.sqrt(1-rho-rg-rp)*rng.standard_normal(M); H[i]=y<ND.inv_cdf(x[key])
    return H
M=30000; Ht=scen('pr',M,SEED+100)
hv=[np.all(Ht[t],axis=0) for t in tk]; cw=np.sum(hv,axis=0)
def J(cw): return cw.mean()+(cw>0).mean()
cur=J(cw); t0=time.time(); it=0
sig=lambda t:tuple(sorted(t)); sigs=collections.Counter(sig(t) for t in tk)
while time.time()-t0<SECS:
    it+=1
    if R.random()<0.5:
        a=R.randrange(NF,N); j=R.randrange(SIZES[a]); q=R.randrange(n); old=tk[a][j]
        if q==old: continue
        add(old,-1)
        ok=legal(tk[a],q,SIZES[a],skip=j)
        if not ok: add(old,1); continue
        ta=tk[a][:]; ta[j]=q
        if sigs[sig(ta)]: add(old,1); continue
        ha=np.all(Ht[ta],axis=0); nc=cw-hv[a]+ha; nv=J(nc)
        if nv>=cur:
            sigs[sig(tk[a])]-=1; add(q,1); tk[a]=ta; hv[a]=ha; cw=nc; cur=nv; sigs[sig(ta)]+=1
        else: add(old,1)
    else:
        a=R.randrange(NF,N); b=R.randrange(NF,N)
        if a==b: continue
        i=R.randrange(SIZES[a]); j=R.randrange(SIZES[b]); x=tk[a][i]; y=tk[b][j]
        if x==y: continue
        add(x,-1); add(y,-1)
        ok=legal(tk[a],y,SIZES[a],skip=i) and legal(tk[b],x,SIZES[b],skip=j)
        add(x,1); add(y,1)
        if not ok: continue
        ta=tk[a][:]; ta[i]=y; tb=tk[b][:]; tb[j]=x
        if sig(ta)==sig(tb) or sigs[sig(ta)] or sigs[sig(tb)]: continue
        ha=np.all(Ht[ta],axis=0); hb=np.all(Ht[tb],axis=0)
        nc=cw-hv[a]-hv[b]+ha+hb; nv=J(nc)
        if nv>=cur:
            sigs[sig(tk[a])]-=1; sigs[sig(tk[b])]-=1; tk[a],tk[b]=ta,tb; hv[a],hv[b]=ha,hb; cw=nc; cur=nv; sigs[sig(ta)]+=1; sigs[sig(tb)]+=1
def ev(key,s=9,M=200000):
    H=scen(key,M,s); w2=np.zeros(M); ref=np.zeros(M); bys=collections.defaultdict(float)
    for t in tk:
        hh=H[t].sum(axis=0); win=hh==len(t); w2+=win; ref+=hh==len(t)-1; bys[len(t)]+=win.mean()
    return dict(p1=round(float((w2>=1).mean()),3), ew=round(float(w2.mean()),3), bys={k:round(v,3) for k,v in bys.items()}, ref=round(float(ref.mean()),2))
print('iters',it,'est',ev('pr'),'market',ev('fair'))
uc=collections.Counter(P[i]['p'] for t in tk for i in t); print('player tickets',sorted(uc.items(),key=lambda x:-x[1]))
pc2=collections.Counter(i for t in tk for i in t); print('pairs used',len(pc2),'max pair',max(pc2.values()),'players used',len(uc))
ov=[len({pid[i] for i in a}&{pid[i] for i in b})/min(len(a),len(b)) for x,a in enumerate(tk) for b in tk[x+1:]]
print('avg shared players share',round(sum(ov)/len(ov),3))
json.dump({'tk':tk},open(CFG['out'],'w'))
