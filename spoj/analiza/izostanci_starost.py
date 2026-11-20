"""Izostanci po starosti (20.11.2026): novi 0–2, srednji 3–5, vrlo stari 6+ propuštenih utakmica. python3 spoj/analiza/izostanci_starost.py"""
import io, os, sys, contextlib, collections
R='/home/claude/Euroleague'
src=open(f'{R}/spoj/analiza/an3.py',encoding='utf8').read(); src=src[:src.index("print('  po stavci (p3")]
g={'__file__':f'{R}/spoj/analiza/an3.py','__name__':'x'}
with contextlib.redirect_stdout(io.StringIO()): exec(compile(src,'an3','exec'),g)
F,byteam=g['F'],g['byteam']
td={t:sorted(D) for t,D in byteam.items()}
cache={}
def izost(team,dan):
    if (team,dan) in cache: return cache[(team,dan)]
    pre=collections.defaultdict(list)
    for d in td[team]:
        if d<dan:
            for r in byteam[team][d]:
                if r['min']>0: pre[r['k']].append(r['min'])
    rot={k:sum(m)/len(m) for k,m in pre.items() if len(m)>=3 and sum(m)/len(m)>=10}
    danas={r['k'] for r in byteam[team].get(dan,[]) if r['min']>0}
    b=[0.0,0.0,0.0]
    for k,m in rot.items():
        if k in danas: continue
        prop=0
        for d in reversed([d for d in td[team] if d<dan]):
            if any(r['k']==k and r['min']>0 for r in byteam[team][d]): break
            prop+=1
        b[0 if prop<=2 else 1 if prop<=5 else 2]+=m
    cache[(team,dan)]=tuple(b); return cache[(team,dan)]
for x in F: x['iz']=izost(x['team'],x['dan']); x['mix']=(x['p3']+1-x['pm'])/2
def red(S,nm):
    if not S: print(f'  {nm:58} n=0'); return
    n=len(S); y=sum(x['y'] for x in S)/n; mk=sum(1-x['tr'] for x in S)/n
    print(f"  {nm:58} n={n:4} ispod {y:5.1%} | tržište {mk:5.1%} | razlika {y-mk:+.1%}")
for nm,us in (('sve',lambda x:True),('jaki po proseku (mix>=.60, kvota>=1.6)',lambda x:x['mix']>=.6 and x['u']>=1.6)):
    print('==',nm)
    B=[x for x in F if us(x)]
    red([x for x in B if sum(x['iz'])<20],'bez izostanaka (<20 min)')
    red([x for x in B if x['iz'][0]>=35],'novi (0–2 utakmice) ≥35')
    red([x for x in B if x['iz'][0]<20 and x['iz'][1]>=35],'srednji (3–5 utakmica) ≥35, novi <20')
    red([x for x in B if x['iz'][0]<20 and x['iz'][1]<20 and x['iz'][2]>=35],'samo vrlo stari (6+ utakmica) ≥35')
    red([x for x in B if x['iz'][0]+x['iz'][1]<35 and sum(x['iz'])>=35],'ukupno ≥35, ali novi+srednji <35 (vrlo stari dopunjuju)')
    red([x for x in B if x['iz'][0]+x['iz'][1]>=35],'novi+srednji ≥35 (filter bez vrlo starih)')
