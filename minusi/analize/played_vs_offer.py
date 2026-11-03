import json,numpy as np,collections,re,unicodedata
L=json.load(open('legs.json')); D=json.load(open('ds_all.json'))
def nk(x):
    t=unicodedata.normalize('NFD',str(x)); t=''.join(c for c in t if unicodedata.category(c)!='Mn').lower(); return re.sub(r'[^a-z ]','',t.replace('-',' ').replace('.',' ')).split()[-1]
off=collections.defaultdict(list)
for d in D: off[d['day']].append(d)
print('dan | ponuda prolaz | odigrani parovi (jedinstveni) prolaz | po mestima na tiketima')
tot=collections.Counter()
for day in sorted({l['gday'] for l in L}):
    ll=[l for l in L if l['gday']==day and l['res'] in('hit','miss')]
    u={}
    for l in ll: u[(l['p'],l['stat'],l['line'])]=l['res']=='hit'
    o=off.get(day)
    print(day, f"{np.mean([d['hit'] for d in o]):.3f} (n={len(o)})" if o else '   -    ', f"{np.mean(list(u.values())):.3f} (n={len(u)})", f"{np.mean([l['res']=='hit' for l in ll]):.3f} (n={len(ll)})")
    tot['u']+=len(u); tot['uh']+=sum(u.values()); tot['m']+=len(ll); tot['mh']+=sum(l['res']=='hit' for l in ll)
    if o: tot['o']+=len(o); tot['oh']+=sum(d['hit'] for d in o); tot['u2']+=len(u); tot['uh2']+=sum(u.values()); tot['m2']+=len(ll); tot['mh2']+=sum(l['res']=='hit' for l in ll)
print('UKUPNO jedinstveni',round(tot['uh']/tot['u'],3),tot['u'],'po mestima',round(tot['mh']/tot['m'],3),tot['m'])
print('dani sa ponudom: ponuda',round(tot['oh']/tot['o'],3),'jedinstveni odigrani',round(tot['uh2']/tot['u2'],3),'po mestima',round(tot['mh2']/tot['m2'],3))
# odds of played legs
print('prosecna kvota odigranih',np.mean([l['odds'] for l in L]).round(3))
# claude plans real app pr
st=json.load(open('/home/claude/app/v6/state_now.json')); rows=json.load(open('/home/claude/form/rows.json'))
byk=collections.defaultdict(list)
for r in rows: byk[r['k']].append(r)
def find(name,day):
    t=unicodedata.normalize('NFD',name); t=''.join(c for c in t if unicodedata.category(c)!='Mn').lower(); t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t); k=' '.join(w for w in t.split() if w not in {'jr','sr','ii','iii','iv'})
    cand=[kk for kk in byk if kk==k] or [kk for kk in byk if kk.split()[-1]==k.split()[-1] and kk[0]==k[0]]
    for kk in cand:
        x=[r for r in byk[kk] if r['d'][:10]==day]
        if x: return x[0]
    return None
U={}
for p in st['claudePlans']:
    day='2026-10-23' if 'r7d3' in p['id'] else '2026-10-22'
    for t in p['tickets']:
        for l in t['legs']:
            r=find(l['p'],day)
            if not r: continue
            U[(day,l['p'],l['s'],l['l'])]=(l['pr'],l['u'],1 if r[l['s']]<l['l'] else 0)
pr=np.array([v[0] for v in U.values()]); y=np.array([v[2] for v in U.values()])
print('Planovi kolo 7 (stvarne vrednosti iz aplikacije): parova',len(U),'prolaz',y.mean().round(3),'prosecna sansa',pr.mean().round(3))
for lo,hi in ((0,0.55),(0.55,0.6),(0.6,0.65),(0.65,1)):
    m=(pr>=lo)&(pr<hi)
    if m.sum(): print(f'  sansa [{lo},{hi}) n={m.sum()} prolaz={y[m].mean():.3f}')
