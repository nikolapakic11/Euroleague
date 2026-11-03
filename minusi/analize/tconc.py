import json,numpy as np,collections,math
L=json.load(open('legs.json'))
T=collections.defaultdict(list)
for l in L: T[l['tid']].append(l)
rows=[]
for tid,ls in T.items():
    v=[l for l in ls if l['res'] in('hit','miss')]
    if len(v)<6: continue
    g=collections.Counter(l['g'] for l in v); mx=max(g.values()); ng=len(g)
    miss=sum(l['res']=='miss' for l in v); hr=np.mean([l['res']=='hit' for l in v])
    rows.append(dict(tid=tid,n=len(v),mx=mx,share=mx/len(v),ng=ng,miss=miss,date=ls[0]['date']))
# expected under independence given the day's leg hit rate (po mestima) per day
dayrate={}
for d in {r['date'] for r in rows}:
    v=[l for l in L if l['date']==d and l['res'] in('hit','miss')]; dayrate[d]=np.mean([l['res']=='hit' for l in v])
def grp(lab,f):
    s=[r for r in rows if f(r)]
    if not s: return
    win=np.mean([r['miss']==0 for r in s]); one=np.mean([r['miss']<=1 for r in s])
    exp=np.mean([dayrate[r['date']]**r['n'] for r in s]); exp1=np.mean([dayrate[r['date']]**r['n']+r['n']*dayrate[r['date']]**(r['n']-1)*(1-dayrate[r['date']]) for r in s])
    print(f'{lab:34s} tiketa {len(s):4d} dobitnih {sum(r["miss"]==0 for r in s):3d} ({win:.3f}, ocek. {exp:.3f})  0-1 promasaj {one:.3f} (ocek. {exp1:.3f})  prosek promasaja {np.mean([r["miss"] for r in s]):.2f}')
print('udeo najzastupljenije utakmice na tiketu:')
grp('do 25% (npr. najvise 2 od 8)',lambda r:r['share']<=0.25)
grp('26-40%',lambda r:0.25<r['share']<=0.4)
grp('preko 40%',lambda r:r['share']>0.4)
print('broj razlicitih utakmica:')
for a,b in ((1,3),(4,4),(5,5),(6,20)): grp(f'{a}-{b} utakmica',lambda r,a=a,b=b:a<=r['ng']<=b)
print('svi',len(rows))
# varijansa promasaja vs binomna
for n in (8,10):
    s=[r for r in rows if r['n']==n]
    if s:
        m=np.mean([r['miss'] for r in s]); p=m/n
        print(n,'parova: tiketa',len(s),'var promasaja',np.var([r['miss'] for r in s]).round(2),'binomna',round(n*p*(1-p),2))
