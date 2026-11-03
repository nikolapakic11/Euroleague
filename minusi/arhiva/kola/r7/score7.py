import json, re, unicodedata, math, sys
from statistics import NormalDist
ND=NormalDist()
S=json.load(open('season.json')); pl=S['pl']; team=S['team']
off=json.load(open(sys.argv[1]))
SUF={'jr','sr','ii','iii','iv'}
def na(x):
    x=unicodedata.normalize('NFD',x); x=''.join(c for c in x if unicodedata.category(c)!='Mn').lower().replace('đ','dj')
    x=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',x).replace('-',' ').replace('.',' ').replace("'",'')
    return ' '.join(t for t in re.sub(r'[^a-z ]','',x).split() if t not in SUF)
def find(name):
    k=na(name)
    if k in pl: return pl[k]
    t=k.split(); c=[kk for kk in pl if kk.split() and kk.split()[-1]==t[-1] and kk.split()[0][:1]==t[0][:1]]
    return pl[c[0]] if len(c)==1 else None
NORM={'Crvena zvezda':'Crvena Zvezda','Bayern Munich':'Bayern'}
TM={'Anadolu Efes':'EFES','Besiktas':'BESIKTAS','Bayern':'BAYERN','Dubai':'DUBAI','Maccabi Tel Aviv':'MACCABI','Real Madrid':'REAL','Panathinaikos':'PANATHINAIKOS','Baskonia':'BASKONIA','Olimpia Milano':'MILAN','Barcelona':'BARCELONA','Partizan':'PARTIZAN','Crvena Zvezda':'CRVENA'}
OPP={'Anadolu Efes':'Besiktas','Besiktas':'Anadolu Efes','Bayern':'Dubai','Dubai':'Bayern','Maccabi Tel Aviv':'Real Madrid','Real Madrid':'Maccabi Tel Aviv','Panathinaikos':'Baskonia','Baskonia':'Panathinaikos','Olimpia Milano':'Barcelona','Barcelona':'Olimpia Milano','Partizan':'Crvena Zvezda','Crvena Zvezda':'Partizan'}
GAME={'Anadolu Efes':'IST-BES','Besiktas':'IST-BES','Bayern':'MUN-DUB','Dubai':'MUN-DUB','Maccabi Tel Aviv':'TEL-MAD','Real Madrid':'TEL-MAD','Panathinaikos':'PAN-BAS','Baskonia':'PAN-BAS','Olimpia Milano':'MIL-BAR','Barcelona':'MIL-BAR','Partizan':'PAR-RED','Crvena Zvezda':'PAR-RED'}
def tstats(t):
    k=[n for n in team if TM[t] in n][0]; v=team[k]
    return sum(x[1] for x in v)/len(v), sum(x[2] for x in v)/len(v)
exp={t:(tstats(t)[0]+tstats(OPP[t])[1])/2 for t in OPP}
def pois(k,m):
    s=0; term=math.exp(-m)
    for i in range(k+1):
        if i: term*=m/i
        s+=term
    return s
ADJ=json.load(open(sys.argv[2])) if len(sys.argv)>2 else {}
rows=[]
for p in off['picks']:
    t=NORM.get(p['t'],p['t']); s=p['s']; l=p['l']; u=p['u']; o=p.get('o') or u
    if u<1.65: continue
    g=find(p['p'])
    if not g or len(g)<2: continue
    n=len(g); vals=[x[s] for x in g]; mins=[x['min'] for x in g]; avgm=sum(mins)/n
    w=[1.0]*n
    for i in range(max(0,n-3),n): w[i]=1.5
    avg=sum(v*wi for v,wi in zip(vals,w))/sum(w)
    tp,_=tstats(t); env=exp[t]/tp
    m=avg*(env**0.8 if s in 'PA' else 1.0)
    model=ND.cdf((l-m)/(0.35*m+2.5)) if s=='P' else pois(int(math.floor(l)),max(m,0.1))
    h=sum(1 for v in vals if v<l); hist=(h+1)/(n+2)
    fair=(1/u)/((1/u)+(1/o))
    pr=0.35*model+0.35*fair+0.3*hist
    adj=0
    if avgm<=20: adj+=0.02
    if avgm>=27: adj-=0.03
    adj+=max(-0.03,min(0.03,(85-exp[t])*0.006))
    if s=='P' and l<=5.5: adj-=0.025
    if s in 'AS': adj+=0.01
    adj+=ADJ.get(p['p']+'|'+s, ADJ.get(p['p'],0))
    rows.append(dict(c=p['c'],p=p['p'],t=t,s=s,l=l,u=u,o=o,pr=pr+adj,base=pr,fair=fair,h=f"{h}/{n}",vals=vals[-6:],min=round(avgm,1),exp=round(exp[t],1),g=GAME[t],time=p['time']))
rows.sort(key=lambda r:-r['pr'])
json.dump(rows,open('scored.json','w'))
best={}
for r in rows:
    if r['p'] not in best: best[r['p']]=r
B=sorted(best.values(),key=lambda r:-r['pr'])
for i,r in enumerate(B[:45]): print(i, round(r['pr']*100,1), r['p'], r['t'][:10], r['s'], r['l'], r['u'], r['h'], r['vals'], 'min', r['min'], r['g'])
print({t:round(v,1) for t,v in exp.items()})
