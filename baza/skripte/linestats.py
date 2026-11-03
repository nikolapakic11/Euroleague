import json,re,unicodedata,collections
rows=json.load(open('/home/claude/form/rows.json'))
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',t); t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t)
    return ' '.join(w for w in t.split() if w not in SUF)
byk=collections.defaultdict(list)
for r in rows: byk[r['k']].append(r)
keys=list(byk)
def find(name,day):
    k=nk(name); c=[k] if k in byk else [kk for kk in keys if kk.split()[-1]==k.split()[-1] and kk[0]==k[0]]
    for kk in c:
        x=[r for r in byk[kk] if r['d'][:10]==day]
        if x: return x[0]
    return None
items=[]
D=json.load(open('/home/claude/form/ds_all.json'))
for d in D: items.append(dict(day=d['day'],s=d['s'],l=d['l'],u=d['u'],fair=d['fair'],hit=d['hit']))
for day,f in (('2026-10-27','/home/claude/r8/offer3_raw.json'),('2026-10-28','/home/claude/r8b/offer2_raw.json'),('2026-10-29','/home/claude/r9/offer_raw.json')):
    seen=set()
    for p in json.load(open(f))['picks']:
        k=(nk(p['p']),p['s'])
        if k in seen: continue
        seen.add(k); r=find(p['p'],day)
        if not r or r['min']<=0: continue
        items.append(dict(day=day,s=p['s'],l=p['l'],u=p['u'],fair=(1/p['u'])/((1/p['u'])+(1/p['o'])),hit=1 if r[p['s']]<p['l'] else 0))
print('ukupno',len(items),collections.Counter(i['day'] for i in items))
out={}
for s in 'ASP':
    for l in sorted({i['l'] for i in items if i['s']==s}):
        I=[i for i in items if i['s']==s and i['l']==l]
        if len(I)<5 and s=='P': continue
        h=sum(i['hit'] for i in I); u=sum(i['u'] for i in I)/len(I); f=sum(i['fair'] for i in I)/len(I)
        roi=sum((i['u']-1) if i['hit'] else -1 for i in I)/len(I)
        be=sum(1/i['u'] for i in I)/len(I)
        out[s+str(l)]=[len(I),h,round(f,3),round(u,2),round(roi,3),round(be,3)]
        if s!='P': print(s,l,'n',len(I),'proslo',h,round(h/len(I),3),'kvote kazu',round(f,3),'prosecna kvota',round(u,2),'ROI',round(roi,3))
json.dump({'at':'2026-10-29','n':len(items),'src':'cela ponuda AdmiralBeta, minusi, 8.10. do 29.10.','t':out},open('/home/claude/lines/linestats.json','w'))
