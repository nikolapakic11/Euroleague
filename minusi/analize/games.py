import json,numpy as np,collections,itertools,math
D=json.load(open('ds_all.json')); L=json.load(open('legs.json'))
# 1) korelacija minusa iz ponude
gid=lambda d: tuple(sorted((d['team'],d['opp'])))
cat=collections.defaultdict(lambda:[0,0,0,0])  # n pairs, both, a, b
byday=collections.defaultdict(list)
for d in D: byday[d['day']].append(d)
for day,ds in byday.items():
    for a,b in itertools.combinations(ds,2):
        if a['p']==b['p']: c='isti igrac'
        elif gid(a)!=gid(b): c='razlicite utakmice'
        elif a['team']==b['team']: c='isti tim'
        else: c='protivnicki timovi'
        x=cat[c]; x[0]+=1; x[1]+=a['hit']*b['hit']; x[2]+=a['hit']; x[3]+=b['hit']
for c,(n,bb,a,b) in cat.items():
    pa,pb,pab=a/n,b/n,bb/n
    phi=(pab-pa*pb)/math.sqrt(pa*(1-pa)*pb*(1-pb))
    print(f'{c:20s} parova {n:6d} oba prosla {pab:.3f} ocekivano nezavisno {pa*pb:.3f} korelacija {phi:+.3f}')
# po statistici u istoj utakmici
cat2=collections.defaultdict(lambda:[0,0,0,0])
for day,ds in byday.items():
    for a,b in itertools.combinations(ds,2):
        if a['p']==b['p'] or gid(a)!=gid(b): continue
        c=('isti tim' if a['team']==b['team'] else 'protivnici')+' '+''.join(sorted(a['s']+b['s']))
        x=cat2[c]; x[0]+=1; x[1]+=a['hit']*b['hit']; x[2]+=a['hit']; x[3]+=b['hit']
for c,(n,bb,a,b) in sorted(cat2.items()):
    pa,pb,pab=a/n,b/n,bb/n; phi=(pab-pa*pb)/math.sqrt(pa*(1-pa)*pb*(1-pb))
    print(f'   {c:16s} n={n:5d} korelacija {phi:+.3f}')
# 2) prolaz minusa po utakmici: raspon po utakmicama
gm=collections.defaultdict(list)
for d in D: gm[(d['day'],gid(d))].append(d['hit'])
r=sorted([(np.mean(v),len(v),k) for k,v in gm.items() if len(v)>=6])
print('utakmica',len(r),'prolaz minusa po utakmici: najlosije',[(round(a,2),n) for a,n,k in r[:5]],'najbolje',[(round(a,2),n) for a,n,k in r[-5:]])
print('sd po utakmici',np.std([a for a,n,k in r]).round(3),'ocekivano iz binomne', np.mean([math.sqrt(0.57*0.43/n) for a,n,k in r]).round(3))
# veza sa ukupnim poenima
gt=collections.defaultdict(list)
for d in D: gt[(d['day'],gid(d))].append((d['gtot'],d['hit']))
pts=[(v[0][0],np.mean([h for _,h in v]),len(v)) for v in gt.values() if len(v)>=6]
for lo,hi in ((0,155),(155,165),(165,175),(175,185),(185,400)):
    s=[(h,n) for t,h,n in pts if lo<=t<hi]
    if s: print(f'  ukupno poena [{lo},{hi}) utakmica {len(s)} prolaz minusa {sum(h*n for h,n in s)/sum(n for h,n in s):.3f}')
