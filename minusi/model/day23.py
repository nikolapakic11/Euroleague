import json,math,collections,numpy as np
exec(open('robust.py').read().split('days=sorted')[0])
st=json.load(open('/home/claude/app/v6/state_after_record.json'))
T=[t for t in st['tickets'] if t['date']=='2026-10-23']
legs=collections.Counter((l['p'],l['stat'],l['line']) for t in T for l in t['legs'])
res=st['results']
def r(l): 
    ls=str(int(l[2])) if float(l[2]).is_integer() else repr(float(l[2]))
    return res.get('|'.join(['7',l[0].lower(),l[1],ls]))
D23=[d for d in D if d['day']=='2026-10-23']
P=(1.5,1.5,0.2,0.15,0.1)
for d in D23: d['z0']=v4z(d); d['z1']=v4z(d)+adj(d,*P)
o0=sorted(D23,key=lambda d:-d['z0']); o1=sorted(D23,key=lambda d:-d['z1'])
rk0={(d['p'],d['s']):i+1 for i,d in enumerate(o0)}; rk1={(d['p'],d['s']):i+1 for i,d in enumerate(o1)}
import unicodedata,re
def nk(x):
    x=unicodedata.normalize('NFD',x); x=''.join(c for c in x if unicodedata.category(c)!='Mn').lower(); return re.sub(r'[^a-z ]','',x.replace('-',' ')).split()[-1]
byl={(nk(d['p']),d['s']):d for d in D23}
hits=0;tot=0
print(f"{'igrac':24s} st  lin  akt  tiketa  rang_v5 rang_novi  of   pace  close")
rows=[]
for (p,s,l),c in sorted(legs.items(),key=lambda x:-x[1]):
    x=r((p,s,l)); a=x['actual'] if x else None; h=(a is not None and a<l)
    d=byl.get((nk(p),s))
    tot+=1; hits+=h
    pace=(d['exp_team']/d['lgp']) if d and d['exp_team'] else None
    rows.append((p,s,l,a,h,c,rk0.get((d['p'],d['s'])) if d else None,rk1.get((d['p'],d['s'])) if d else None,d['of'] if d else None,pace,abs(d['spread'])<=5 if d else None))
for x in rows: print(f"{x[0]:24s} {x[1]} {x[2]:5} {str(x[3]):>4} {'OK' if x[4] else 'XX'} {x[5]:3d}   {str(x[6]):>4} {str(x[7]):>4}  {x[8] and round(x[8],2)} {x[9] and round(x[9],2)} {x[10]}")
print('parova',tot,'proslo',hits, 'od',len(D23),'ponudjenih; ukupno prolaz ponude',np.mean([d['hit'] for d in D23]).round(3))
k=len(D23)//4
print('top25 v5',np.mean([d['hit'] for d in o0[:k]]).round(3),'top25 novi',np.mean([d['hit'] for d in o1[:k]]).round(3))
print('novi top 15:',[(d['p'],d['s'],d['l'],d['act'],d['hit']) for d in o1[:15]])
# ticket-weighted pass
lw=sum(c for (p,s,l),c in legs.items()); lh=sum(c for (p,s,l),c in legs.items() if (r((p,s,l)) or {}).get('actual') is not None and r((p,s,l))['actual']<l)
print('mesta na tiketima',lw,'prolaz po mestima',round(lh/lw,3))
# ticket miss distribution
cnt=collections.Counter()
for t in T:
    m=sum(1 for l in t['legs'] if (r((l['p'],l['stat'],l['line'])) or {}).get('actual') is not None and r((l['p'],l['stat'],l['line']))['actual']>l['line'])
    cnt[(len(t['legs']),min(m,4))]+=1
print(sorted(cnt.items()))
