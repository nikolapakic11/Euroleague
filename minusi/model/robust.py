import json,math,numpy as np,collections
D=json.load(open('ds_all.json')); y=np.array([d['hit'] for d in D],float)
def lgt(p): p=min(.98,max(.02,p)); return math.log(p/(1-p))
def v4z(d):
    pm=d['pm']; cv=d['cv']; z=0.16+0.5*lgt(d['fair'])
    z+={'A':0.12,'S':0.08,'P':0}[d['s']]+(0.12 if d['s']=='P' and d['l']>=10.5 else 0)
    z+=-0.25 if pm<12 else -0.08 if pm<17 else 0 if pm<21 else 0.15 if pm<25 else 0.12
    if cv is not None: z-=0.4*max(0,min(1,(cv-0.2)/0.15))
    return z
def adj(d,a,b,c,f,db):
    pace=(d['exp_team']/d['lgp']) if d['exp_team'] else 1
    z=-a*(d['of']-1)-b*(pace-1)+(c if abs(d['spread'])<=5 else 0)
    r=(d['rate3']/d['rate']) if d['rate']>0 else 1
    if r>1.3: z-=f
    if d['spread']<-5 and d['st']<0.5: z-=db
    return z
days=sorted({d['day'] for d in D})
for P in ((0,0,0,0,0),(1.5,1.5,0.2,0,0),(1.5,1.5,0.2,0.15,0),(1.5,1.5,0.2,0.15,0.1),(2,2,0.15,0.15,0)):
    sc=[v4z(d)+adj(d,*P) for d in D]
    per=[];tops=[];t40=[]
    for dd in days:
        te=[i for i,d in enumerate(D) if d['day']==dd]; o=sorted(te,key=lambda i:-sc[i]); k=max(1,len(te)//4)
        per.append(round(float(np.mean([y[i] for i in o[:k]])),2)); tops+=[y[i] for i in o[:k]]; t40+=[y[i] for i in o[:int(len(te)*.4)]]
    # calibration-ish: brier of sigmoid
    p=1/(1+np.exp(-np.array(sc))); ll=np.mean(y*np.log(p)+(1-y)*np.log(1-p))
    print(P,'top25',round(np.mean(tops),3),'top40',round(np.mean(t40),3),'ll',round(ll,4),'po danima',per)
print({dd:sum(1 for d in D if d['day']==dd) for dd in days})
