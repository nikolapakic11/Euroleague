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
# Hibrid (od 12.11.2026, osnova; provera unazad 16 dana: isplata/ulog 1,78 prema 1,12 kod raspršenog): 'jezgro' tiketa
# (najkraći, podrazumevano trećina) sme da uzima samo najjače parove: nivo A + najboljih 'jtop' po vrednosti (pr×kvota);
# ostali tiketi su mešani. cfg: "jezgro": broj tiketa jezgra (podrazumevano N//3, 0 = isključeno), "jtop": veličina bazena jezgra.
# Ravnomerna raspodela (od 14.11.2026, stalno pravilo, odluka Nikole; analiza minusi/analiza/raspodela.py i raspodela2.py):
# svaki par iz bazena ide na približno isti broj tiketa (prosek ± 'tol', podrazumevano 10%, po igraču). Unutar užeg bazena rang ne
# razlikuje sigurnije parove (5 najzastupljenijih po danu 51% naspram 57% svih), a ravnomerno je na 24 dana vratilo 206%
# uloga prema 155% kako je odigrano. Jezgro je tada podrazumevano isključeno (nije postojano: bolje u 7 od 23 dana).
# "ravnomerno": 0 vraća staro ponašanje (maxu/pmax iz cfg, jezgro trećina tiketa).
RAV=CFG.get('ravnomerno',1)
NJ=CFG.get('jezgro',0 if RAV else N//3); JTOP=CFG.get('jtop',max(12,n//4))
MINU=0; PMIN=0
if RAV:
    # ravnomerno po IGRAČU (njegove stavke dele jednu kvotu), da isti igrač ne bude na mnogo tiketa preko više stavki
    _slots=sum(SIZES[NF:]); _np=len({x['p'] for x in P}); _avg=_slots/_np; TOL=CFG.get('tol',0.1)
    PMAX=max(1,math.ceil(_avg*(1+TOL))); PMIN=max(0,math.floor(_avg*(1-TOL))); MAXU=PMAX
    print(f'ravnomerno: {_np} igrača ({n} stavki), {_slots} mesta, prosek {_avg:.1f} po igraču ({_avg/max(1,N-NF):.0%} tiketa), dozvoljeno {PMIN}-{PMAX}')
    if _avg/max(1,N-NF)>0.32: print('UPOZORENJE: bazen je mali, svaki igrač bi bio na više od 32% tiketa; dodaj igrače ili smanji broj/dužinu tiketa')
_rv=sorted(range(n),key=lambda i:-P[i]['pr']*P[i]['u'])
COREPOOL=set(_rv[:JTOP])|{i for i in range(n) if P[i].get('nivo')=='A'}
CORE=set(sorted(range(NF,N),key=lambda k:(SIZES[k],k))[:NJ])
pm=np.mean([x['pr'] for x in P]); w=[math.exp(K*(x['pr']-pm)) for x in P]
players=sorted({x['p'] for x in P}); pid=[players.index(x['p']) for x in P]
use=[0]*n; puse=[0]*len(players)
def legal(t,i,L,skip=-1,kk=None):
    if i in LOCK: return False
    if kk in CORE and i not in COREPOOL: return False
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
order=sorted(range(NF,N),key=lambda k:(k not in CORE,-SIZES[k]))
for k in order:
    L=SIZES[k]
    for att in range(3000):
        t=[]
        for _ in range(L):
            c=[i for i in range(n) if legal(t,i,L,kk=k)]
            if not c: break
            if RAV: ws=[(max(0.05,PMAX-puse[pid[i]]))**3*w[i]**0.25 for i in c]
            else: ws=[w[i]**0.5*((MAXU-use[i])/MAXU)*((PMAX-puse[pid[i]])/PMAX)**3 for i in c]
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
# kv (od 7.11.2026): dobitak tiketa se broji sa težinom (proizvod kvota / 1,9 po paru)^kv; 0 = kao ranije (broj dobitnih
# tiketa), 1 = očekivana isplata. Provera (spoj/provera/izvestaj.md): parovi birani po vrednosti prolaze češće i plaćaju više.
KV=CFG.get('kv',0)
def wt(t): return math.prod(P[i]['u']/1.9 for i in t)**KV if KV else 1.0
wts=[wt(t) for t in tk]
hv=[np.all(Ht[t],axis=0) for t in tk]; cw=np.sum([w*h for w,h in zip(wts,hv)],axis=0)
def J(cw): return cw.mean()+(cw>0).mean()
cur=J(cw); t0=time.time(); it=0
sig=lambda t:tuple(sorted(t)); sigs=collections.Counter(sig(t) for t in tk)
while time.time()-t0<SECS:
    it+=1
    if R.random()<0.5:
        a=R.randrange(NF,N); j=R.randrange(SIZES[a]); q=R.randrange(n); old=tk[a][j]
        if q==old: continue
        if pid[q]!=pid[old] and puse[pid[old]]-1<PMIN: continue
        add(old,-1)
        ok=legal(tk[a],q,SIZES[a],skip=j,kk=a)
        if not ok: add(old,1); continue
        ta=tk[a][:]; ta[j]=q
        if sigs[sig(ta)]: add(old,1); continue
        ha=np.all(Ht[ta],axis=0); wa=wt(ta); nc=cw-wts[a]*hv[a]+wa*ha; nv=J(nc)
        if nv>=cur:
            sigs[sig(tk[a])]-=1; add(q,1); tk[a]=ta; hv[a]=ha; wts[a]=wa; cw=nc; cur=nv; sigs[sig(ta)]+=1
        else: add(old,1)
    else:
        a=R.randrange(NF,N); b=R.randrange(NF,N)
        if a==b: continue
        i=R.randrange(SIZES[a]); j=R.randrange(SIZES[b]); x=tk[a][i]; y=tk[b][j]
        if x==y: continue
        add(x,-1); add(y,-1)
        ok=legal(tk[a],y,SIZES[a],skip=i,kk=a) and legal(tk[b],x,SIZES[b],skip=j,kk=b)
        add(x,1); add(y,1)
        if not ok: continue
        ta=tk[a][:]; ta[i]=y; tb=tk[b][:]; tb[j]=x
        if sig(ta)==sig(tb) or sigs[sig(ta)] or sigs[sig(tb)]: continue
        ha=np.all(Ht[ta],axis=0); hb=np.all(Ht[tb],axis=0); wa=wt(ta); wb=wt(tb)
        nc=cw-wts[a]*hv[a]-wts[b]*hv[b]+wa*ha+wb*hb; nv=J(nc)
        if nv>=cur:
            sigs[sig(tk[a])]-=1; sigs[sig(tk[b])]-=1; tk[a],tk[b]=ta,tb; hv[a],hv[b]=ha,hb; wts[a],wts[b]=wa,wb; cw=nc; cur=nv; sigs[sig(ta)]+=1; sigs[sig(tb)]+=1
def ev(key,s=9,M=200000):
    H=scen(key,M,s); w2=np.zeros(M); ref=np.zeros(M); isp=np.zeros(M); bys=collections.defaultdict(float)
    for t in tk:
        hh=H[t].sum(axis=0); win=hh==len(t); w2+=win; ref+=hh==len(t)-1; bys[len(t)]+=win.mean(); isp+=win*math.prod(P[i]['u'] for i in t)
    # isplata: očekivani povraćaj po ulogu 1 na svakom tiketu (1,0 = izlaz na nulu; bez povraćaja i bonusa)
    return dict(p1=round(float((w2>=1).mean()),3), ew=round(float(w2.mean()),3), bys={k:round(v,3) for k,v in bys.items()}, ref=round(float(ref.mean()),2), isplata=round(float(isp.mean()/len(tk)),3))
print('iters',it,'est',ev('pr'),'market',ev('fair'))
_u=collections.Counter(P[i]['p'] for t in tk for i in t); print('ponavljanje igrača: najmanje',min(_u.get(p,0) for p in players),'najviše',max(_u.values()),'neiskorišćenih',sum(1 for p in players if not _u.get(p)))
uc=collections.Counter(P[i]['p'] for t in tk for i in t); print('player tickets',sorted(uc.items(),key=lambda x:-x[1]))
pc2=collections.Counter(i for t in tk for i in t); print('pairs used',len(pc2),'max pair',max(pc2.values()),'players used',len(uc))
ov=[len({pid[i] for i in a}&{pid[i] for i in b})/min(len(a),len(b)) for x,a in enumerate(tk) for b in tk[x+1:]]
print('avg shared players share',round(sum(ov)/len(ov),3))
json.dump({'tk':tk},open(CFG['out'],'w'))
