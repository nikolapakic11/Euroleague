import json,math,numpy as np,collections
exec(open('/home/claude/form/robust.py').read().split('days=sorted')[0])
P6=(1.5,1.5,0.2,0.15,0.1)
def sig(z): return 1/(1+math.exp(-z))
for d in D:
    d['pr5']=max(0.3,min(0.8,sig(v4z(d)))); d['pr6']=max(0.3,min(0.8,sig(v4z(d)+adj(d,*P6))))
    d['ev5']=d['pr5']*d['u']-1; d['ev6']=d['pr6']*d['u']-1
def auc(s,yy):
    s=np.array(s); yy=np.array(yy); o=np.argsort(s); r=np.empty(len(s)); r[o]=np.arange(1,len(s)+1)
    n1=yy.sum(); n0=len(yy)-n1; return (r[yy==1].sum()-n1*(n1+1)/2)/(n1*n0)
def roi(idx): return np.mean([D[i]['u']-1 if D[i]['hit'] else -1 for i in idx])
def table(name,key,edges,subset):
    print(f'-- {name}')
    for lo,hi in zip(edges[:-1],edges[1:]):
        idx=[i for i in subset if lo<=D[i][key]<hi]
        if idx: print(f"   [{lo:.2f},{hi:.2f}) n={len(idx):4d} predvidjeno={np.mean([D[i][key] for i in idx]) if key.startswith('pr') else 0:.3f} proslo={np.mean([D[i]['hit'] for i in idx]):.3f} kvota_fer={np.mean([D[i]['fair'] for i in idx]):.3f} ROI_pojedinacno={roi(idx):+.3f}")
ALL=list(range(len(D))); OOS=[i for i,d in enumerate(D) if d['day']>='2026-10-22']; INS=[i for i,d in enumerate(D) if d['day']<'2026-10-22']
print('N',len(D),'OOS',len(OOS))
for nm,sub in (('sve',ALL),('van uzorka 22-23.10',OOS)):
    yy=[D[i]['hit'] for i in sub]
    print(nm,'AUC kvote',round(auc([D[i]['fair'] for i in sub],yy),3),'AUC sansa v5',round(auc([D[i]['pr5'] for i in sub],yy),3),'AUC v6',round(auc([D[i]['pr6'] for i in sub],yy),3),
          'AUC vrednost v5',round(auc([D[i]['ev5'] for i in sub],yy),3))
table('Sansa v5, sve','pr5',[0,0.5,0.55,0.6,0.65,1],ALL)
table('Sansa v5, van uzorka','pr5',[0,0.5,0.55,0.6,0.65,1],OOS)
table('Sansa v6, sve','pr6',[0,0.5,0.55,0.6,0.65,1],ALL)
table('Vrednost v5 (nivoi aplikacije), sve','ev5',[-9,-0.08,-0.04,0,0.03,9],ALL)
table('Vrednost v5, van uzorka','ev5',[-9,-0.08,-0.04,0,0.03,9],OOS)
table('Samo kvote (fer verovatnoca)','fair',[0,0.45,0.48,0.51,0.54,1],ALL)
# within-day thirds
for key in ('fair','pr5','pr6','ev5'):
    top=[];bot=[];mid=[]
    for dd in sorted({d['day'] for d in D}):
        te=sorted([i for i,d in enumerate(D) if d['day']==dd],key=lambda i:-D[i][key]); k=len(te)//3
        top+=te[:k]; mid+=te[k:2*k]; bot+=te[2*k:]
    print(f"po danu trecine po {key}: gornja {np.mean([D[i]['hit'] for i in top]):.3f} srednja {np.mean([D[i]['hit'] for i in mid]):.3f} donja {np.mean([D[i]['hit'] for i in bot]):.3f}")
print('ukupno prolaz ponude',np.mean([d['hit'] for d in D]).round(3),'fer',np.mean([d['fair'] for d in D]).round(3),'prosecna kvota',np.mean([d['u'] for d in D]).round(3))
for dd in sorted({d['day'] for d in D}):
    sub=[d for d in D if d['day']==dd]; print(dd,len(sub),round(np.mean([d['hit'] for d in sub]),3),round(np.mean([d['fair'] for d in sub]),3))
