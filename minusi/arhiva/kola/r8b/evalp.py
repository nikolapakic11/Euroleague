import json,math,sys,numpy as np
from statistics import NormalDist
ND=NormalDist()
def ev(self,planf,stake,M=100000):
    P=json.load(open(self)); tk=json.load(open(planf))['tk']
    used=sorted({i for t in tk for i in t}); players=sorted({P[i]['p'] for i in used}); games=sorted({P[i]['g'] for i in used}); teams=sorted({P[i]['t'] for i in used})
    BON={8:.16,10:.26,12:.36}
    pay=np.array([stake*math.prod(P[i]['u'] for i in t)*(1+BON[len(t)]) for t in tk])
    out={}
    for nm,f in (('trziste',lambda e:e['fair']),('sredina',lambda e:(e['pr']+e['fair'])/2),('aplikacija',lambda e:e['pr'])):
        rng=np.random.default_rng(5); D=rng.standard_normal(M); G={g:rng.standard_normal(M) for g in games}; T={t:rng.standard_normal(M) for t in teams}; PL={p:rng.standard_normal(M) for p in players}
        H={}
        for i in used:
            e=P[i]; y=math.sqrt(.006)*D+math.sqrt(.02)*G[e['g']]+math.sqrt(.02)*T[e['t']]+math.sqrt(.35)*PL[e['p']]+math.sqrt(1-.396)*rng.standard_normal(M)
            H[i]=y<ND.inv_cdf(f(e))
        W=np.array([np.all([H[i] for i in t],axis=0) for t in tk]); ret=(W*pay[:,None]).sum(axis=0)
        out[nm]=(round(float((W.sum(0)>=1).mean()),3),round(float(ret.mean()/(stake*len(tk))),2))
    return out,round(float(np.median(pay))),round(np.mean([P[i]['pr'] for t in tk for i in t]),3)
for n,st in (('A',50),('B',50),('D',50)):
    print(n,ev(f'/home/claude/r8b/sel_{n}.json',f'/home/claude/r8b/plan_{n}.json',st))
