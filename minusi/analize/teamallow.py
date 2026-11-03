import json,collections,numpy as np,statistics as stt
rows=json.load(open('/home/claude/form/rows.json')); D=json.load(open('ds_all.json'))
# per team per game: what opponents got (P,S,A totals) and team's own
tg=collections.defaultdict(dict)
for r in rows:
    g=tg[r['opp']].setdefault(r['g'],{'day':r['d'][:10],'P':0,'S':0,'A':0}); g['P']+=r['P']; g['S']+=r['S']; g['A']+=r['A']
def allowed(team,day,stat,last=None):
    gs=sorted([v for v in tg[team].values() if v['day']<day],key=lambda v:v['day'])
    if last: gs=gs[-last:]
    return stt.mean(v[stat] for v in gs) if gs else None
def league(day,stat):
    v=[allowed(t,day,stat) for t in tg]; v=[x for x in v if x]; return stt.mean(v)
cache={}
y=[]; rowsS=[]
for d in D:
    if d['s'] not in 'SA': continue
    k=(d['day'],d['s'])
    if k not in cache: cache[k]=league(d['day'],d['s'])
    a=allowed(d['opp'],d['day'],d['s']); a4=allowed(d['opp'],d['day'],d['s'],4)
    if not a: continue
    rowsS.append(dict(s=d['s'],hit=d['hit'],fair=d['fair'],r=a/cache[k],r4=a4/cache[k],of=d['of']))
for s in 'SA':
    R=[x for x in rowsS if x['s']==s]
    print('==',s,'n',len(R),'prolaz',round(np.mean([x['hit'] for x in R]),3))
    for key,lab in (('r','sezona'),('r4','poslednje 4'),('of','pozicija (v6)')):
        for lo,hi in ((0,0.93),(0.93,0.98),(0.98,1.02),(1.02,1.07),(1.07,9)):
            I=[x for x in R if lo<=x[key]<hi]
            if I: print(f'  {lab:14s} [{lo},{hi}) n={len(I):3d} prolaz {np.mean([x["hit"] for x in I]):.3f} kvote {np.mean([x["fair"] for x in I]):.3f}')
    # correlation
    for key in ('r','r4','of'):
        print('  korelacija sa prolazom',key,round(np.corrcoef([x[key] for x in R],[x['hit'] for x in R])[0,1],3))
# Zvezda now
day='2026-10-30'
for s in 'SA':
    L=league(day,s)
    print(s,'liga',round(L,1),'RED sezona',round(allowed('RED',day,s),1),'poslednje 4',round(allowed('RED',day,s,4),1))
    tops=sorted(((allowed(t,day,s)/L,allowed(t,day,s,4)/L,t) for t in tg),key=lambda x:x[0])
    print('   najmanje dozvoljava (sezona):',[(t,round(a,2),round(b,2)) for a,b,t in tops[:5]],' najvise:',[(t,round(a,2),round(b,2)) for a,b,t in tops[-4:]])
import math
exec(open('/home/claude/form/robust.py').read().split('days=sorted')[0].replace("D=json.load(open('ds_all.json'))","D2=json.load(open('ds_all.json'))").replace('y=np.array([d[\'hit\'] for d in D],float)',''))
P6=(1.5,1.5,0.2,0.15,0.1)
base=[];DD=[]
for d in D:
    if d['s']!='A': continue
    k=(d['day'],'A'); a=allowed(d['opp'],d['day'],'A')
    if not a: continue
    DD.append((d,v4z(d)+adj(d,*P6),a/cache[k]))
days=sorted({d['day'] for d,_,_ in DD})
for kf in (0,0.5,1.0,1.5,2.0):
    tops=[];bots=[]
    for dd in days:
        te=[(z-kf*(r-1),d['hit']) for d,z,r in DD if d['day']==dd]
        te.sort(key=lambda x:-x[0]); k=max(1,len(te)//3)
        tops+=[h for _,h in te[:k]]; bots+=[h for _,h in te[-k:]]
    print('asistencije, tezina tima',kf,'gornja trecina',round(np.mean(tops),3),'donja',round(np.mean(bots),3),'n',len(tops))
