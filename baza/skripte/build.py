import json,re,unicodedata,collections,statistics as stt,glob,sys,os
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','minusi'))
from putanje import BAZA
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',t); t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t)
    return ' '.join(w for w in t.split() if w not in SUF)
def pn(n):
    if ',' in n: a=n.split(','); return nk(a[1]+' '+a[0])
    return nk(n)
G={g['gameCode']:g for g in json.load(open(BAZA+'/games.json'))['data']}
POS={}
for f in glob.glob(BAZA+'/rosteri/*.json'):
    for x in json.load(open(f)):
        if x.get('type')=='J' and x.get('person'):
            POS[pn(x['person']['name'])]=(x.get('positionName') or '')
def grp(p): return 'G' if p=='Guard' else 'C' if p=='Center' else 'F' if p=='Forward' else '?'
rows=[]
for f in glob.glob(BAZA+'/zapisnici/*.json'):
    gc=int(re.findall(r'\d+',os.path.basename(f))[0]); d=json.load(open(f)); g=G[gc]
    teams=[s['PlayersStats'][0]['Team'] if s['PlayersStats'] else None for s in d['Stats']]
    for si,s in enumerate(d['Stats']):
        for p in s['PlayersStats']:
            mm=p['Minutes']
            if not mm or ':' not in mm: continue
            a,b=mm.split(':'); m=int(a)+int(b)/60
            if m<=0: continue
            tm=p['Team'].strip(); opp=[t for t in teams if t and t.strip()!=tm]
            k=pn(p['Player'])
            rows.append(dict(g=gc,r=g['round'],d=g['date'],team=tm,opp=opp[0].strip() if opp else '',k=k,name=p['Player'],min=m,P=p['Points'],S=p['TotalRebounds'],A=p['Assistances'],st=p.get('IsStarter',0),pos=grp(POS.get(k,''))))
json.dump(rows,open(BAZA+'/rows.json','w'))
print(len(rows), collections.Counter(r['pos'] for r in rows))
