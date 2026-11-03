import json,math,random,collections,time,sys
import numpy as np
from statistics import NormalDist
ND=NormalDist()
CFG=json.loads(sys.argv[1]); P=json.load(open(CFG['sel'])); n=len(P)
SIZES=CFG['sizes']; N=len(SIZES); S=sum(SIZES)
GC=CFG.get('gcaps',{}); TCAP=CFG.get('tcap',2); GCAP=CFG.get('gcap',3); MAXU=CFG['maxu']; MINU=CFG['minu']; SEED=CFG.get('seed',1); SECS=CFG.get('secs',60); K=CFG.get('k',12)
pm=np.mean([x['pr'] for x in P])
w=np.array([math.exp(K*(x['pr']-pm)) for x in P])
# usage targets with caps by player, team and game
cnt=np.clip(np.round(S*w/w.sum()),MINU,MAXU).astype(int)
def fix():
    global cnt
    for _ in range(2000):
        # team/game caps
        ch=False
        for key,cap0 in (('t',TCAP),('g',GCAP)):
            grp=collections.defaultdict(list)
            for i,x in enumerate(P): grp[x[key]].append(i)
            for k,ids in grp.items():
                cap=(GC.get(k,cap0) if key=='g' else cap0)*N
                while cnt[ids].sum()>cap:
                    j=max(ids,key=lambda i:cnt[i]); cnt[j]-=1; ch=True
        d=S-cnt.sum()
        if d==0 and not ch: return
        if d>0:
            # add to best eligible
            order=sorted(range(n),key=lambda i:-w[i]/(cnt[i]+1))
            for i in order:
                tg=sum(cnt[j] for j in range(n) if P[j]['t']==P[i]['t']); gg=sum(cnt[j] for j in range(n) if P[j]['g']==P[i]['g'])
                if cnt[i]<MAXU and tg<TCAP*N and gg<GC.get(P[i]['g'],GCAP)*N: cnt[i]+=1; break
            else: raise SystemExit('cannot place')
        elif d<0:
            i=max(range(n),key=lambda i:cnt[i]/w[i]); cnt[i]-=1
fix()
print('targets',[(P[i]['p'].split()[-1],int(cnt[i])) for i in range(n)], cnt.sum())
def legal(t,i):
    if i in t: return False
    if sum(1 for j in t if P[j]['t']==P[i]['t'])>=TCAP: return False
    if sum(1 for j in t if P[j]['g']==P[i]['g'])>=GC.get(P[i]['g'],GCAP): return False
    return True
def construct(sd):
    R=random.Random(sd); tk=[[] for _ in range(N)]; left=cnt.copy()
    # fill ticket by ticket, choosing items with most remaining need relative to remaining tickets
    order=list(range(N)); R.shuffle(order)
    for idx,k in enumerate(order):
        remT=N-idx
        for _ in range(SIZES[k]):
            c=[i for i in range(n) if left[i]>0 and legal(tk[k],i)]
            if not c: return None
            # urgency: left / remaining tickets
            i=max(c,key=lambda i:left[i]/remT+R.random()*0.3); tk[k].append(i); left[i]-=1
    return tk
tk=None
for sd in range(2000):
    tk=construct(SEED*10000+sd)
    if tk: break
assert tk,'no construct'
teams=sorted({x['t'] for x in P}); ti={t:i for i,t in enumerate(teams)}
games=sorted({x['g'] for x in P}); gi={g:i for i,g in enumerate(games)}
def scen(key,M,s,rho=0.06,rg=0.04):
    rng=np.random.default_rng(s); Z=rng.standard_normal((len(teams),M)); G=rng.standard_normal((len(games),M)); H=np.zeros((n,M),bool)
    for i,x in enumerate(P):
        p=x[key]; y=math.sqrt(rho)*Z[ti[x['t']]]+math.sqrt(rg)*G[gi[x['g']]]+math.sqrt(1-rho-rg)*rng.standard_normal(M); H[i]=y<ND.inv_cdf(p)
    return H
M=30000; Ht=scen('pr',M,SEED+100); R=random.Random(SEED)
hv=[np.all(Ht[t],axis=0) for t in tk]; cw=np.sum(hv,axis=0)
def J(cw): return cw.mean()+ (cw>0).mean()
cur=J(cw); t0=time.time(); it=0
sig=lambda t:tuple(sorted(t))
while time.time()-t0<SECS:
    it+=1
    a=R.randrange(N); b=R.randrange(N)
    if a==b: continue
    i=R.randrange(SIZES[a]); j=R.randrange(SIZES[b]); x=tk[a][i]; y=tk[b][j]
    if x==y: continue
    ta=tk[a][:i]+tk[a][i+1:]; tb=tk[b][:j]+tk[b][j+1:]
    if not (legal(ta,y) and legal(tb,x)): continue
    ta.append(y); tb.append(x)
    sa,sb=sig(ta),sig(tb); others={sig(t) for k,t in enumerate(tk) if k not in (a,b)}
    if sa in others or sb in others or sa==sb: continue
    ha=np.all(Ht[ta],axis=0); hb=np.all(Ht[tb],axis=0)
    nc=cw-hv[a]-hv[b]+ha+hb; nv=J(nc)
    if nv>=cur: tk[a],tk[b]=ta,tb; hv[a],hv[b]=ha,hb; cw=nc; cur=nv
def ev(key,s=9,M=200000):
    H=scen(key,M,s); w=np.zeros(M); ref=np.zeros(M); w10=np.zeros(M); w12=np.zeros(M)
    for k,t in enumerate(tk):
        h=H[t].sum(axis=0); win=h==len(t); w+=win; ref+=h==len(t)-1
        if len(t)==10: w10+=win
        else: w12+=win
    return dict(p1=round(float((w>=1).mean()),3), ew=round(float(w.mean()),3), ew10=round(float(w10.mean()),3), ew12=round(float(w12.mean()),3), p2=round(float((w>=2).mean()),3), ref=round(float(ref.mean()),2))
print('iters',it,'est',ev('pr'),'market',ev('fair'))
uc=collections.Counter(i for t in tk for i in t)
print('usage',[(P[i]['p'].split()[-1],uc[i]) for i in range(n)])
gc=collections.Counter(g for t in tk for g in {P[i]['g'] for i in t}); print('tickets per game',dict(gc))
odds=[math.prod(P[i]['u'] for i in t) for t in tk]
BON={10:0.26,12:0.36}
try: print('odds10',round(min(odds[:20])),round(max(odds[:20])),'odds12',round(min(odds[20:])),round(max(odds[20:])))
except Exception: pass
json.dump({'tk':tk},open(CFG['out'],'w'))
ov=[len(set(a)&set(b))/min(len(a),len(b)) for x,a in enumerate(tk) for b in tk[x+1:]]
print('avg shared share',round(sum(ov)/len(ov),3),'max usage share',round(max(uc.values())/N,3))
