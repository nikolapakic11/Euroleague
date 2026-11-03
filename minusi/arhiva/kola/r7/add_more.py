import json, math, random, collections, time
import numpy as np
from statistics import NormalDist
ND=NormalDist()
rows=json.load(open('scored.json'))
excl={"Juancho Hernangomez","Konstantinos Mitoglou","Guerschon Yabusele","Mathias Lessort","Jimmy Clark III","Jordan Loyd","Nigel Hayes-Davis","Keaton Wallace","Collin Malcolm","Cameron Payne","Kevin Punter","Umoja Gibson","Justin Robinson"}
capx={"Clement Frisch":3,"Dejan Davidovac":3,"Josh Nebo":3,"Matthew Strazel":3,"Yam Madar":3,"Kevarrius Hayes":7}
best={}
for r in rows:
    if r['p'] in excl: continue
    if r['p'] not in best: best[r['p']]=r
P=sorted(best.values(),key=lambda r:-r['pr'])[:60]
key=lambda r:(r['c'],r['s'])
ix={key(r):i for i,r in enumerate(P)}
old=json.load(open('plan25x8.json'))['tickets']
oldt=[[ix[(l['c'],l['s'])] for l in t['legs']] for t in old]
base=collections.Counter(i for t in oldt for i in t)
cap=[min(8 if k<10 else 7 if k<25 else 5, capx.get(P[k]['p'],99)) for k in range(len(P))]
teams=sorted({r['t'] for r in P}); ti={t:i for i,t in enumerate(teams)}
def scen(M,s,key='pr',rho=0.06):
    rng=np.random.default_rng(s); Z=rng.standard_normal((len(teams),M)); H=np.zeros((len(P),M),bool)
    for i,r in enumerate(P):
        p=min(0.88,max(0.1,r[key])); y=math.sqrt(rho)*Z[ti[r['t']]]+math.sqrt(1-rho)*rng.standard_normal(M); H[i]=y<ND.inv_cdf(p)
    return H
H=scen(8000,3)
oldwin=np.zeros(H.shape[1],bool)
for t in oldt: oldwin|=np.all(H[t],axis=0)
def legal(t):
    if len({P[i]['p'] for i in t})<len(t): return False
    if max(collections.Counter(P[i]['t'] for i in t).values())>3: return False
    if max(collections.Counter(P[i]['g'] for i in t).values())>3: return False
    if sum(1 for i in t if P[i]['g']=='IST-BES')>2: return False
    return True
def ok_caps(new):
    nc=collections.Counter(i for t in new for i in t)
    return all(base[i]+nc[i]<=max(cap[i],base[i]) for i in nc)
R=random.Random(5)
def rand_ticket():
    while True:
        w=[max(0.01,P[i]['pr']-0.45)*(1.0 if base[i]<cap[i] else 0) for i in range(len(P))]
        t=[]
        cand=list(range(len(P)))
        while len(t)<8:
            i=R.choices(cand,weights=w)[0]
            if i in t: continue
            if legal(t+[i]): t.append(i)
            else: w[i]=0
            if sum(w)==0: break
        if len(t)==8: return t
new=[]; tries=0
while len(new)<5 and tries<20000:
    tries+=1
    t=rand_ticket()
    if ok_caps(new+[t]): new.append(t)
print('init tries', tries, len(new), 'room', sum(max(0,cap[i]-base[i]) for i in range(len(P))))
def score(new):
    w=oldwin.copy()
    for t in new: w|=np.all(H[t],axis=0)
    return w.mean()
cur=score(new); t0=time.time()
while time.time()-t0<40:
    a=R.randrange(5); j=R.randrange(8); i=R.randrange(len(P))
    t=new[a][:]; t[j]=i
    if not legal(t): continue
    cand=new[:a]+[t]+new[a+1:]
    if not ok_caps(cand): continue
    v=score(cand)
    if v>=cur: new,cur=cand,v
print('P(>=1 win) old', round(oldwin.mean(),3), 'old+new', round(cur,3))
tot=base+collections.Counter(i for t in new for i in t)
print('max total', max(tot.values()), [(P[i]['p'],tot[i]) for i,_ in tot.most_common(12)])
for t in new: print([(P[i]['p'],P[i]['s'],P[i]['l']) for i in t], round(math.prod(P[i]['u'] for i in t)))
out={'v':1,'round':'7','tickets':[{'stake':100,'legs':[{'c':P[i]['c'],'p':P[i]['p'],'t':P[i]['t'],'s':P[i]['s'],'l':P[i]['l'],'u':P[i]['u']} for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['p']))]} for t in new]}
json.dump(out,open('plan5x8_extra.json','w'),ensure_ascii=False,separators=(',',':'))
