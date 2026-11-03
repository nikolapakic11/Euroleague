import json, re, unicodedata, math, collections
from statistics import NormalDist
ND=NormalDist()
S=json.load(open('/home/claude/r7/season.json')); pl=S['pl']; team=S['team']
SUF={'jr','sr','ii','iii','iv'}
def na(x):
    x=unicodedata.normalize('NFD',x); x=''.join(c for c in x if unicodedata.category(c)!='Mn').lower().replace('đ','dj')
    x=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',x).replace('-',' ').replace('.',' ').replace("'",'')
    return ' '.join(t for t in re.sub(r'[^a-z ]','',x).split() if t not in SUF)
KEYS=list(pl.keys())
def find(name):
    k=na(name)
    if k in pl: return k
    t=k.split()
    c=[kk for kk in KEYS if kk.split() and kk.split()[-1]==t[-1] and kk.split()[0][:1]==t[0][:1]]
    if len(c)==1: return c[0]
    c=[kk for kk in KEYS if kk.split() and kk.split()[-1]==t[-1]]
    if len(c)==1: return c[0]
    c=[kk for kk in KEYS if t[0] in kk.split() and (len(t)<2 or t[1][:3] in kk)]
    return c[0] if len(c)==1 else None
# team game logs with dates: rebuild from player logs is hard; use team list (no dates) -> approximate env with all games (slight leakage) -> instead compute per-date from box via player logs is complex; keep simple
OFF={'2026-10-08':'/mnt/user-data/uploads/attachment-f069d4c3.txt','2026-10-09':'/mnt/user-data/uploads/attachment-32a2be47.txt','2026-10-13':'/mnt/user-data/uploads/attachment-974065fc.txt','2026-10-14':'/mnt/user-data/uploads/attachment-4016429c.txt','2026-10-15':'/mnt/user-data/uploads/attachment-e27a929c.txt','2026-10-16':'/mnt/user-data/uploads/attachment.txt'}
NORM={'Crvena zvezda':'Crvena Zvezda','Bayern Munich':'Bayern','Zalgiris':'Zalgiris Kaunas'}
def pois(k,m):
    s=0; term=math.exp(-m)
    for i in range(k+1):
        if i: term*=m/i
        s+=term
    return s
rows=[]; miss=collections.Counter()
for day,f in OFF.items():
    d=json.load(open(f))
    for p in d['picks']:
        k=find(p['p'])
        if not k: miss[p['p']]+=1; continue
        g=pl[k]; prior=[x for x in g if x['d']<day]; cur=[x for x in g if x['d']==day]
        if not cur: continue   # did not play / not in box -> void
        x=cur[0]; s=p['s']; l=p['l']; u=p['u']; o=p.get('o') or None
        if x['min']<1: continue
        actual=x[s]; hit=1 if actual<l else 0
        n=len(prior)
        r=dict(day=day,p=p['p'],t=NORM.get(p['t'],p['t']),s=s,l=l,u=u,o=o,actual=actual,hit=hit,min_act=x['min'],n=n)
        if n:
            vals=[y[s] for y in prior]; mins=[y['min'] for y in prior]
            r['avg']=sum(vals)/n; r['avgmin']=sum(mins)/n
            r['l3']=sum(vals[-3:])/len(vals[-3:]); r['l3min']=sum(mins[-3:])/len(mins[-3:])
            r['hist']=sum(1 for v in vals if v<l)/n
            r['sd']=(sum((v-r['avg'])**2 for v in vals)/n)**0.5 if n>1 else None
            m=r['avg']
            r['model']=ND.cdf((l-m)/(0.35*m+2.5)) if s=='P' else pois(int(math.floor(l)),max(m,0.1))
            r['gap']=l-r['avg']
            r['per36']=r['avg']/max(r['avgmin'],1)*36
        r['fair']=(1/u)/((1/u)+(1/o)) if o else 1/u/1.08
        r['imp']=1/u
        rows.append(r)
json.dump(rows,open('dsA.json','w'))
print(len(rows), 'unmatched', miss.most_common(10))
print(collections.Counter(r['day'] for r in rows))
