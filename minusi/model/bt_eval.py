"""Walk-forward evaluacija varijanti procene verovatnoće minusa. Ulaz: RADNO/bt_data.json (backtest.py)."""
import json,os,sys,math,collections
import numpy as np
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import BAZA,RADNO
from math import erf,sqrt
rows=[r for r in json.load(open(BAZA+'/rows.json')) if r['min']>0]
byk=collections.defaultdict(list)
for r in rows: byk[r['k']].append(r)
D=json.load(open(RADNO+'/bt_data.json'))
def ncdf(x): return 0.5*(1+erf(x/sqrt(2)))
def own(x):
    h=[q for q in byk[x['k']] if q['d'][:10]<x['day']][-8:]
    if len(h)<3: return None
    v=np.array([q[x['s']] for q in h],float); m=v.mean(); sd=max(v.std(ddof=1),0.8 if x['s']!='P' else 2.0)
    w=np.array([0.5**(len(h)-1-i)*0+1 for i in range(len(h))])
    return ncdf((x['l']-m)/sd)   # P(val<line) (aprox. neprekidno)
def lgt(p): p=min(max(p,1e-3),1-1e-3); return math.log(p/(1-p))
for x in D:
    x['fair']=(1/x['u'])/((1/x['u'])+(1/x['o'])); x['own']=own(x)
D=[x for x in D if x['own'] is not None]
days=sorted({x['day'] for x in D}); print('parova',len(D),'dana',len(days))
def fit(tr,feats,l2=1.0,it=300):
    X=np.array([[1]+[f(x) for f in feats] for x in tr]); y=np.array([x['hit'] for x in tr],float)
    w=np.zeros(X.shape[1])
    for _ in range(it):
        p=1/(1+np.exp(-X@w)); g=X.T@(p-y)+l2*np.r_[0,w[1:]]; H=(X.T*(p*(1-p)))@X+l2*np.eye(len(w)); w-=np.linalg.solve(H,g)
    return w
def pred(w,feats,x): return 1/(1+math.exp(-(w[0]+sum(wi*f(x) for wi,f in zip(w[1:],feats)))))
V={
 'trziste':None,
 'trziste*0.93':'shr',
 'LR fair':[lambda x:lgt(x['fair'])],
 'LR fair+own':[lambda x:lgt(x['fair']),lambda x:lgt(x['own'])],
 'LR fair+own+stat':[lambda x:lgt(x['fair']),lambda x:lgt(x['own']),lambda x:x['s']=='S',lambda x:x['s']=='A'],
 'staro 0.16+.45+.45':'old',
}
res={}
for name,fe in V.items():
    P=[];Y=[];T=[]
    for d in days[3:]:
        tr=[x for x in D if x['day']<d]; te=[x for x in D if x['day']==d]
        if len(tr)<150: continue
        if fe is None: ps=[x['fair'] for x in te]
        elif fe=='shr': ps=[x['fair']*0.93 for x in te]
        elif fe=='old': ps=[1/(1+math.exp(-(0.16+0.45*lgt(x['fair'])+0.45*lgt(x['own'])))) for x in te]
        else:
            w=fit(tr,fe); ps=[pred(w,fe,x) for x in te]
        for x,p in zip(te,ps): P.append(p);Y.append(x['hit']);T.append((x['day'],p,x['hit'],x['u']))
    P=np.array(P);Y=np.array(Y)
    br=((P-Y)**2).mean(); ll=-(Y*np.log(P)+(1-Y)*np.log(1-P)).mean()
    # top-N po danu: 15 najverovatnijih po danu
    tops=[];
    for d in days:
        t=sorted([z for z in T if z[0]==d],key=lambda z:-z[1])[:25]
        if t: tops.append(np.mean([z[2] for z in t]))
    print(f'{name:22s} n={len(Y)} Brier={br:.4f} LL={ll:.4f} sred.P={P.mean():.3f} stvarno={Y.mean():.3f} top25 pogodak={np.mean(tops):.3f}')
