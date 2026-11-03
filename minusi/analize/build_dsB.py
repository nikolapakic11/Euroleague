import json, re, unicodedata, math, collections, sys
sys.path.insert(0,'.')
from statistics import NormalDist
exec(open('build_ds.py').read().split("# team game logs")[0])
pat=r'(<script type="application/json" id="state">)(.*?)(</script>)'
L=json.loads(re.search(pat,open('/mnt/user-data/outputs/evroliga-minusi.html').read(),re.S).group(2))
seen={}
for t in L['tickets']:
    day=t['date']
    for l in t['legs']:
        key=(day,l['p'],l['stat'],l['line'])
        seen.setdefault(key,{'u':l['odds'],'cnt':0,'team':l.get('team')}); seen[key]['cnt']+=1
rows=[]
for (day,p,s,l),v in seen.items():
    k=find(p)
    if not k: continue
    g=pl[k]; prior=[x for x in g if x['d']<day]; cur=[x for x in g if x['d']==day]
    if not cur or cur[0]['min']<1: continue
    x=cur[0]; n=len(prior)
    r=dict(day=day,p=p,s=s,l=l,u=v['u'],cnt=v['cnt'],hit=1 if x[s]<l else 0,actual=x[s],min_act=x['min'],n=n)
    if n:
        vals=[y[s] for y in prior]; mins=[y['min'] for y in prior]
        r['avg']=sum(vals)/n; r['avgmin']=sum(mins)/n; r['gap']=l-r['avg']; r['hist']=sum(1 for vv in vals if vv<l)/n
    rows.append(r)
json.dump(rows,open('dsB.json','w')); print(len(rows), collections.Counter(r['day'] for r in rows))
