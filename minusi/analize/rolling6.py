import json,math,numpy as np,itertools
exec(open('/home/claude/form/robust.py').read().split('days=sorted')[0])
days=sorted({d['day'] for d in D})
grid=list(itertools.product((0,1,1.5,2,3),(0,1,1.5,2,3),(0,0.1,0.2,0.3),(0,0.15),(0,0.1)))
base=np.array([v4z(d) for d in D]); AD={P:np.array([adj(d,*P) for d in D]) for P in grid}
def ll(idx,z): p=1/(1+np.exp(-z[idx])); yy=y[idx]; return np.mean(yy*np.log(p)+(1-yy)*np.log(1-p))
def topk(idx,z,f=0.25):
    out=[]
    for dd in sorted({D[i]['day'] for i in idx}):
        te=[i for i in idx if D[i]['day']==dd]; o=sorted(te,key=lambda i:-z[i]); out+=[y[i] for i in o[:max(1,int(len(te)*f))]]
    return out
T0=[];T1=[];K0=[];K1=[];B0=[];B1=[]
for k in range(3,len(days)):
    tr=[i for i,d in enumerate(D) if d['day']<days[k]]; te=[i for i,d in enumerate(D) if d['day']==days[k]]
    best=max(grid,key=lambda P: ll(tr,base+AD[P]))
    z1=base+AD[best]
    T0+=topk(te,base); T1+=topk(te,z1); K0.append(ll(te,base)*len(te)); K1.append(ll(te,z1)*len(te))
    o0=sorted(te,key=lambda i:-base[i]); o1=sorted(te,key=lambda i:-z1[i]); n3=len(te)//3
    B0+=[y[i] for i in o0[-n3:]]; B1+=[y[i] for i in o1[-n3:]]
    print(days[k],'izabrano',best,'top25 staro',round(np.mean(topk(te,base)),3),'novo',round(np.mean(topk(te,z1)),3))
n=sum(1 for d in D if d['day']>=days[3])
print('VAN UZORKA (dani 4-8): top25 staro',round(np.mean(T0),3),'novo',round(np.mean(T1),3),'| donja trecina staro',round(np.mean(B0),3),'novo',round(np.mean(B1),3),'| logloss',round(sum(K0)/n,4),round(sum(K1)/n,4),'| prolaz svih',round(np.mean([d['hit'] for d in D if d['day']>=days[3]]),3))
