import json,math,collections,numpy as np
from statistics import NormalDist
ND=NormalDist()
T=json.load(open('/home/claude/r8/played92.json'))
S=json.load(open('/home/claude/r8/sel8h.json'))
info={}
for e in S: info[(e['p'],e['s'],e['l'])]=e
legs=sorted({(l['p'],l['stat'],l['line']) for t in T for l in t['legs']})
miss=[k for k in legs if k not in info]; print('bez procene',miss)
L=[info[k] for k in legs]; li={k:i for i,k in enumerate(legs)}
players=sorted({e['p'] for e in L}); teams=sorted({e['t'] for e in L}); games=sorted({e['g'] for e in L})
BON={7:.11,8:.16,9:.21,10:.26,12:.36}
tick=[[li[(l['p'],l['stat'],l['line'])] for l in t['legs']] for t in T]
odds=[math.prod(l['odds'] for l in t['legs']) for t in T]; stake=[t['stake'] for t in T]; n=[len(t['legs']) for t in T]
pay=np.array([s*o*(1+BON[k]) for s,o,k in zip(stake,odds,n)])
def sim(pk,M=200000,seed=1,rd=0.006,rg=0.02,rt=0.02,rp=0.35):
    rng=np.random.default_rng(seed)
    Dd=rng.standard_normal(M); G=rng.standard_normal((len(games),M)); Tm=rng.standard_normal((len(teams),M)); PL=rng.standard_normal((len(players),M))
    H=np.zeros((len(L),M),bool)
    for i,e in enumerate(L):
        p=pk(e); y=math.sqrt(rd)*Dd+math.sqrt(rg)*G[games.index(e['g'])]+math.sqrt(rt)*Tm[teams.index(e['t'])]+math.sqrt(rp)*PL[players.index(e['p'])]+math.sqrt(1-rd-rg-rt-rp)*rng.standard_normal(M)
        H[i]=y<ND.inv_cdf(p)
    W=np.zeros((len(T),M),bool); one=np.zeros((len(T),M),bool)
    for k,t in enumerate(tick):
        hh=H[t].sum(axis=0); W[k]=hh==len(t); one[k]=hh==len(t)-1
    ret=(W*pay[:,None]).sum(axis=0)
    ref=(one*np.array([278 if s==100 else 139 for s in stake])[:,None]).sum(axis=0)
    return W,one,ret,ref,H
for nm,pk in (('kvote (trziste)',lambda e:e['fair']),('sredina (kao dosad u sezoni)',lambda e:(e['pr']+e['fair'])/2),('procena aplikacije',lambda e:e['pr'])):
    W,one,ret,ref,H=sim(pk)
    wins=W.sum(axis=0); by={k:W[[i for i in range(len(T)) if n[i]==k]].any(axis=0).mean() for k in (8,10,12)}
    tot=ret+ref
    print(f"== {nm}: prosecan par {np.mean([pk(e) for e in L]):.3f}")
    print(f"   bar 1 dobitni {np.mean(wins>=1):.3f} | bar 2 {np.mean(wins>=2):.3f} | ocek. dobitnih {wins.mean():.2f} | bar jedna osmica {by[8]:.3f}, desetka {by[10]:.3f}, dvanaestica {by[12]:.3f}")
    print(f"   povrat >= ulog 6085: {np.mean(tot>=6085):.3f} | >=20000: {np.mean(tot>=20000):.3f} | >=50000 {np.mean(tot>=50000):.3f} | medijana {np.median(tot):.0f} | ocekivano {tot.mean():.0f} | ocek. tiketa sa 1 promasajem {one.sum(axis=0).mean():.1f}")
print('isplate: osmica po 100 min/med/max',[round(x) for x in np.percentile(pay[[i for i in range(len(T)) if n[i]==8 and stake[i]==100]],[0,50,100])],
      'desetka',[round(x) for x in np.percentile(pay[[i for i in range(len(T)) if n[i]==10]],[0,50,100])],'dvanaestica',[round(x) for x in np.percentile(pay[[i for i in range(len(T)) if n[i]==12]],[0,50,100])])
# exposure
pc=collections.Counter(l['p'] for t in T for l in t['legs'])
pd=collections.defaultdict(set)
for t in T:
    for l in t['legs']: pd[l['p']].add((l['stat'],l['line']))
print('igraci na najvise tiketa:'); 
for p,c in pc.most_common(15): print('  ',p,c,sorted(pd[p]),round(np.mean([info[(p,s,l)]['pr'] for s,l in pd[p]]),3))
gc=collections.Counter(info[(l['p'],l['stat'],l['line'])]['g'] for t in T for l in t['legs']); print('mesta po utakmici',gc)
gt=collections.Counter(); 
for t in T:
    for g in {info[(l['p'],l['stat'],l['line'])]['g'] for l in t['legs']}: gt[g]+=1
print('tiketa koji zavise od utakmice',gt)
