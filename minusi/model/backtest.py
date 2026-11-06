"""Backtest modela za minuse unazad (walk-forward): svaki dan se procenjuje samo iz utakmica pre tog dana.
Skuplja sve sačuvane Admiral ponude (arhiva + baza/ponude/admiral), dodaje ishode iz baza/rows.json i
sprema skup parova u RADNO/bt_data.json. Upotreba: python3 -I backtest.py"""
import json,glob,re,os,sys,unicodedata,collections,math,statistics as stt
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import ROOT,BAZA,MINUSI,RADNO
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r"[.']",'',t); t=re.sub(r'-',' ',t); t=re.sub(r'[^a-z ]','',t); return ' '.join(w for w in t.split() if w not in SUF)
rows=[r for r in json.load(open(BAZA+'/rows.json')) if r['min']>0]
for r in rows: r['day']=r['d'][:10]
byk=collections.defaultdict(list)
for r in rows: byk[r['k']].append(r)
for k in byk: byk[k].sort(key=lambda r:r['d'])
files=sorted(glob.glob(MINUSI+'/arhiva/kola/*/offer*.json')+glob.glob(BAZA+'/ponude/admiral/*.json'))
D={}   # (dan, igrac, stat, granica) -> poslednja ponuda
for f in files:
    try: o=json.load(open(f))
    except Exception: continue
    pk=o.get('picks') if isinstance(o,dict) else None
    if not pk: continue
    for p in pk:
        m=re.search(r'(\d+)\. (\d+)\. (\d{4})',p['time'])
        if not m: continue
        day=f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
        D[(day,nk(p['p']),p['s'],p['l'])]=dict(day=day,k=nk(p['p']),p=p['p'],t=p['t'],s=p['s'],l=p['l'],u=p['u'],o=p['o'])
# ishodi
out=[]
for key,x in D.items():
    r=[q for q in byk.get(x['k'],[]) if q['day']==x['day']]
    if not r: continue          # nije igrao: par se vraća
    x['val']=r[0][x['s']]; x['hit']=int(x['val']<x['l']); x['opp']=r[0]['opp']; x['team']=r[0]['team']
    x['hist_n']=sum(1 for q in byk[x['k']] if q['day']<x['day'])
    out.append(x)
out.sort(key=lambda x:(x['day'],x['p'],x['s'],x['l']))
json.dump(out,open(RADNO+'/bt_data.json','w'),ensure_ascii=False)
c=collections.Counter(x['day'] for x in out)
print('parova sa ishodom',len(out),'dana',len(c)); [print(d,n,round(sum(x['hit'] for x in out if x['day']==d)/n,3)) for d,n in sorted(c.items())]
