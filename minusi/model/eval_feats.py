import json,math,collections,numpy as np
D=json.load(open('ds_all.json'))
def lgt(p): p=min(.98,max(.02,p)); return math.log(p/(1-p))
y=np.array([d['hit'] for d in D],float)
print('N',len(D),'base hit',y.mean().round(3),'fair',np.mean([d['fair'] for d in D]).round(3))
def bucket(name,f,edges):
    vals=[f(d) for d in D]
    for lo,hi in zip(edges[:-1],edges[1:]):
        idx=[i for i,v in enumerate(vals) if v is not None and lo<=v<hi]
        if idx: print(f"  {name} [{lo},{hi}) n={len(idx):4d} hit={y[idx].mean():.3f} fair={np.mean([D[i]['fair'] for i in idx]):.3f}")
print('-- opp positional factor'); bucket('of',lambda d:d['of'],[0,0.92,0.97,1.03,1.08,9])
print('-- expected team pts vs league (pace proxy)'); bucket('pace',lambda d:(d['exp_team']/d['lgp']) if d['exp_team'] else None,[0,0.95,0.98,1.02,1.05,9])
print('-- form minutes last3/season'); bucket('m3',lambda d:d['m3']/d['pm'],[0,0.85,0.95,1.05,1.15,9])
print('-- form rate last3/season'); bucket('r3',lambda d:(d['rate3']/d['rate']) if d['rate']>0 else None,[0,0.7,0.9,1.1,1.3,99])
print('-- last3 under count'); bucket('u3',lambda d:d['under3'],[0,1,2,3,4])
print('-- season avg vs line (margin %)'); bucket('marg',lambda d:(d['l']-d['avg'])/max(d['l'],1),[-9,-0.15,-0.05,0.05,0.15,9])
print('-- bench (st<0.5) vs starters'); bucket('st',lambda d:d['st'],[0,0.5,1.01])
print('-- spread x role: favorite bench'); 
for lab,f in (('fav bench',lambda d:d['spread']>5 and d['st']<0.5),('fav starter',lambda d:d['spread']>5 and d['st']>=0.5),('dog bench',lambda d:d['spread']<-5 and d['st']<0.5),('dog starter',lambda d:d['spread']<-5 and d['st']>=0.5),('close',lambda d:abs(d['spread'])<=5)):
    idx=[i for i,d in enumerate(D) if f(d)]; print(f"  {lab:12s} n={len(idx)} hit={y[idx].mean():.3f}")
print('-- actual game total (post-hoc, diagnostic)'); bucket('gtot',lambda d:d['gtot'],[0,155,165,175,185,999])
print('-- position'); 
for pos in 'GFC':
    idx=[i for i,d in enumerate(D) if d['pos']==pos]; print(f"  {pos} n={len(idx)} hit={y[idx].mean():.3f}")
# logistic models
def feats(d,extra):
    lf=lgt(d['fair']); pm=d['pm']; cv=d['cv']
    f=[1,lf,d['s']=='A',d['s']=='S',d['s']=='P' and d['l']>=10.5,pm>=25,21<=pm<25,pm<15,(cv is not None and cv>0.3)]
    if extra:
        f+=[math.log(d['of']), math.log(d['exp_team']/d['lgp']) if d['exp_team'] else 0, max(-1,min(1,(d['l']-d['avg'])/max(d['l'],1))), math.log(max(0.3,min(3,d['rate3']/d['rate']))) if d['rate']>0 else 0, (d['spread']>5 and d['st']<0.5), (d['spread']<-5 and d['st']>=0.5)]
    return [float(v) for v in f]
def fit(X,yy,lam=4):
    w=np.zeros(X.shape[1])
    for _ in range(60):
        p=1/(1+np.exp(-X@w)); W=p*(1-p); L=lam*np.eye(len(w)); L[0,0]=0
        w+=np.linalg.solve(X.T@(X*W[:,None])+L, X.T@(yy-p)-L@w)
    return w
days=sorted({d['day'] for d in D})
for extra in (False,True):
    ll=[];top=[];allh=[]
    for k in range(3,len(days)):
        tr=[i for i,d in enumerate(D) if d['day']<days[k]]; te=[i for i,d in enumerate(D) if d['day']==days[k]]
        X=np.array([feats(d,extra) for d in D]); w=fit(X[tr],y[tr]); p=1/(1+np.exp(-X[te]@w))
        ll.append(np.mean(y[te]*np.log(p)+(1-y[te])*np.log(1-p))*len(te)); o=np.argsort(-p); kk=max(1,len(te)//4)
        top+=list(y[te][o[:kk]]); allh+=list(y[te])
    n=sum(1 for d in D if d['day']>=days[3])
    print('extra' if extra else 'base ', 'rolling test logloss',round(sum(ll)/n,4),'top25% hit',round(np.mean(top),3),'all',round(np.mean(allh),3))
X=np.array([feats(d,True) for d in D]); w=fit(X,y)
names=['c','lf','A','S','P10','start','mid','low','unst','log_of','log_pace','margin','log_form','favBench','dogStarter']
print({n:round(v,3) for n,v in zip(names,w)})
print('==== standardized')
def feats2(d,extra):
    lf=lgt(d['fair']); pm=d['pm']; cv=d['cv']
    f=[1,lf,d['s']=='A',d['s']=='S',d['s']=='P' and d['l']>=10.5,pm>=25,21<=pm<25,pm<15,(cv is not None and cv>0.3)]
    if extra:
        pace=(d['exp_team']/d['lgp']) if d['exp_team'] else 1
        f+=[(d['of']-1)/0.06,(pace-1)/0.04,abs(d['spread'])<=5]
    return [float(v) for v in f]
for extra in (False,True):
    ll=[];top=[];allh=[];top40=[]
    for k in range(3,len(days)):
        tr=[i for i,d in enumerate(D) if d['day']<days[k]]; te=[i for i,d in enumerate(D) if d['day']==days[k]]
        X=np.array([feats2(d,extra) for d in D]); w=fit(X[tr],y[tr],lam=2); p=1/(1+np.exp(-X[te]@w))
        ll.append(np.mean(y[te]*np.log(p)+(1-y[te])*np.log(1-p))*len(te)); o=np.argsort(-p); kk=max(1,len(te)//4)
        top+=list(y[te][o[:kk]]); top40+=list(y[te][o[:int(len(te)*0.4)]]); allh+=list(y[te])
    n=sum(1 for d in D if d['day']>=days[3])
    print('extra' if extra else 'base ', 'rolling logloss',round(sum(ll)/n,4),'top25%',round(np.mean(top),3),'top40%',round(np.mean(top40),3),'all',round(np.mean(allh),3))
X=np.array([feats2(d,True) for d in D]); w=fit(X,y,lam=2)
print({n:round(v,3) for n,v in zip(['c','lf','A','S','P10','start','mid','low','unst','of_z','pace_z','close'],w)})
# simple: v4 fixed + adjustments
def v4z(d):
    pm=d['pm']; cv=d['cv']; z=0.16+0.5*lgt(d['fair'])
    z+={'A':0.12,'S':0.08,'P':0}[d['s']]+(0.12 if d['s']=='P' and d['l']>=10.5 else 0)
    z+=-0.25 if pm<12 else -0.08 if pm<17 else 0 if pm<21 else 0.15 if pm<25 else 0.12
    if cv is not None: z-=0.4*max(0,min(1,(cv-0.2)/0.15))
    return z
for a,b,c in ((0,0,0),(2,0,0),(0,2,0),(2,2,0),(3,3,0),(2,2,0.15),(3,3,0.2)):
    sc=[v4z(d)-a*(d['of']-1)-b*(((d['exp_team']/d['lgp']) if d['exp_team'] else 1)-1)+(c if abs(d['spread'])<=5 else 0) for d in D]
    tops=[];t40=[]
    for k in range(len(days)):
        te=[i for i,d in enumerate(D) if d['day']==days[k]]; o=sorted(te,key=lambda i:-sc[i])
        tops+=[y[i] for i in o[:max(1,len(te)//4)]]; t40+=[y[i] for i in o[:int(len(te)*0.4)]]
    print(f"a={a} b={b} c={c}: top25% {np.mean(tops):.3f} top40% {np.mean(t40):.3f}")
