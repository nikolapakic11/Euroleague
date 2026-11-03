import json,math,collections,statistics as stt,re,unicodedata
rows=json.load(open('rows.json'))
off=json.load(open('/home/claude/r7d3/offer_el.json'))
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',t); t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t)
    return ' '.join(w for w in t.split() if w not in SUF)
# team game totals
tg=collections.defaultdict(lambda: collections.defaultdict(lambda:[0,0,0]))
for r in rows: a=tg[r['team']][r['g']]; a[0]+=r['P']; a[1]+=r['S']; a[2]+=r['A']
TP={t:stt.mean(v[0] for v in g.values()) for t,g in tg.items()}
# opp allowances by position per game
al=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda:[0,0,0])))
for r in rows:
    if r['pos']=='?': continue
    a=al[r['opp']][r['g']][r['pos']]; a[0]+=r['P']; a[1]+=r['S']; a[2]+=r['A']
lg={}
for pos in 'GFC':
    vals=[al[t][g][pos] for t in al for g in al[t]]
    lg[pos]=[stt.mean(v[i] for v in vals) for i in range(3)]
def oppf(opp,pos,ix):
    gs=al.get(opp,{}); n=len(gs)
    if not n or pos not in 'GFC': return 1.0
    raw=stt.mean(gs[g][pos][ix] for g in gs)/lg[pos][ix]
    return 1+(raw-1)*n/(n+6)
# map offer teams to codes
TM={'Zalgiris Kaunas':'ZAL','Lyon-Villeurbanne':'ASV','Olympiacos':'OLY','Fenerbahce':'ULK','Paris':'PRS','Valencia':'PAM'}
OPP={'ZAL':'ASV','ASV':'ZAL','OLY':'ULK','ULK':'OLY','PRS':'PAM','PAM':'PRS'}
EXP={'ZAL':91.5,'ASV':82.5,'OLY':85.5,'ULK':84.5,'PRS':92.5,'PAM':96.5}
TOT={'ZAL':173.5,'ASV':173.5,'OLY':169.5,'ULK':169.5,'PRS':189.5,'PAM':189.5}
lgTot=2*stt.mean(TP.values())
byk=collections.defaultdict(list)
for r in rows: byk[r['k']].append(r)
for k in byk: byk[k].sort(key=lambda r:r['g'])
def nbcdf(k,mu,rr=8.0):
    if mu<=0: return 1.0
    p=rr/(rr+mu); s=0; pm=p**rr
    for i in range(int(k)+1):
        if i>0: pm*= (i-1+rr)/i*(1-p)
        s+=pm
    return min(1,s)
def ncdf(z): return 0.5*(1+math.erf(z/math.sqrt(2)))
def lgt(p): p=min(.98,max(.02,p)); return math.log(p/(1-p))
out=[]
for pk in off['picks']:
    tc=TM[pk['t']]; k=nk(pk['p']); g=byk.get(k)
    if not g: out.append(dict(p=pk['p'],t=tc,s=pk['s'],l=pk['l'],u=pk['u'],o=pk['o'],note='bez EL utakmica ove sezone')); continue
    ix={'P':0,'S':1,'A':2}[pk['s']]; key=pk['s']
    mins=[r['min'] for r in g]; n=len(g); m_s=stt.mean(mins); last=g[-3:]; m_l=stt.mean(r['min'] for r in last)
    cv=stt.pstdev(mins)/m_s if n>=3 else None
    tot_s=sum(r[key] for r in g); rate_s=tot_s/sum(mins); rate_l=sum(r[key] for r in last)/max(1,sum(r['min'] for r in last))
    rate=0.65*rate_s+0.35*rate_l; mexp=0.6*m_s+0.4*m_l
    st=sum(r['st'] for r in g)/n; pos=g[-1]['pos']
    opp=OPP[tc]; of=oppf(opp,pos,ix)
    pace=(EXP[tc]/TP.get(tc,EXP[tc]))**(0.9 if key in 'PA' else 0.4)
    # blowout / close game minutes
    spread=EXP[tc]-EXP[opp]
    if abs(spread)>=7: mexp*= (0.94 if st>=0.5 else 1.07)
    elif abs(spread)<=2: mexp*= (1.03 if st>=0.5 else 0.96)
    mu=rate*mexp*of*pace
    if key=='P': mp=ncdf((pk['l']-mu)/(0.30*mu+2.5))
    else: mp=nbcdf(math.floor(pk['l']),mu)
    fair=(1/pk['u'])/((1/pk['u'])+(1/pk['o']))
    z=0.16+0.45*lgt(fair)+0.45*lgt(mp)
    if key=='A': z+=0.12
    elif key=='S': z+=0.08
    elif pk['l']>=10.5: z+=0.12
    z+= -0.25 if mexp<12 else -0.08 if mexp<17 else 0 if mexp<21 else 0.15 if mexp<25 else 0.12
    if cv is not None: z-=0.4*max(0,min(1,(cv-0.2)/0.15))
    pr=1/(1+math.exp(-z))
    vals=[r[key] for r in g]
    out.append(dict(p=pk['p'],t=tc,opp=opp,s=key,l=pk['l'],u=pk['u'],o=pk['o'],n=n,m_s=round(m_s,1),m_l=round(m_l,1),st=round(st,2),pos=pos,cv=round(cv,2) if cv else None,avg=round(tot_s/n,1),last=[r[key] for r in last],lastmin=[round(r['min']) for r in last],of=round(of,2),pace=round(pace,2),mu=round(mu,1),mp=round(mp,3),fair=round(fair,3),pr=round(pr,3),hit=f"{sum(1 for v in vals if v<pk['l'])}/{n}"))
json.dump(out,open('cands.json','w'),ensure_ascii=False)
print('league pos allow',lg)
for t in ('ASV','ZAL','OLY','ULK','PRS','PAM'):
    print(t,'allows vs G/F/C (P,S,A):',[[round(oppf(t,pos,i),2) for i in range(3)] for pos in 'GFC'], 'team pts',round(TP.get(t,0),1))
for o in sorted([o for o in out if 'pr' in o],key=lambda o:-o['pr']):
    print(f"{o['p'][:20]:20s} {o['t']} vs {o['opp']} {o['s']} {o['l']:>4} @{o['u']} | {o['pos']} min {o['m_s']}/{o['m_l']} st{o['st']} cv{o['cv']} | avg {o['avg']} last {o['last']} ({o['lastmin']}) hit {o['hit']} | opp {o['of']} pace {o['pace']} mu {o['mu']} model {o['mp']} fair {o['fair']} => {o['pr']}")
for o in out:
    if 'note' in o: print('NOTE',o['p'],o['s'],o['note'])
