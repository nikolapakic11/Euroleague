import json,re,unicodedata,collections,statistics as stt,math
rows=json.load(open('rows.json'))
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r'\b([a-z])\.\s*([a-z])\.',r'\1\2',t); t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t)
    return ' '.join(w for w in t.split() if w not in SUF)
TM={'Anadolu Efes':'IST','Besiktas':'BES','Bayern':'MUN','Bayern Munich':'MUN','Dubai':'DUB','Maccabi Tel Aviv':'TEL','Maccabi T.A.':'TEL','Real Madrid':'MAD','Panathinaikos':'PAN','Baskonia':'BAS','Olimpia Milano':'MIL','Barcelona':'BAR','Partizan':'PAR','Crvena Zvezda':'RED','Crvena zvezda':'RED','Zalgiris Kaunas':'ZAL','Lyon-Villeurbanne':'ASV','Olympiacos':'OLY','Fenerbahce':'ULK','Paris':'PRS','Valencia':'PAM','Hapoel Tel-Aviv':'HTA','Hapoel Tel Aviv':'HTA','Virtus Bologna':'VIR','Monaco':'MON'}
byk=collections.defaultdict(list)
for r in rows: r['day']=r['d'][:10]; byk[r['k']].append(r)
keys=list(byk)
def find(name):
    k=nk(name)
    if k in byk: return k
    t=k.split(); c=[kk for kk in keys if kk.split()[-1]==t[-1] and kk[0]==t[0][0]]
    return c[0] if len(c)==1 else None
# offers
items=[]
for r in json.load(open('/home/claude/an/dsA.json')):
    items.append(dict(day=r['day'],p=r['p'],t=r['t'],s=r['s'],l=r['l'],u=r['u'],o=r['o']))
for day,f in (('2026-10-22','/home/claude/r7c/offer_adm.json'),('2026-10-23','/home/claude/r7d3/offer_el.json')):
    for pk in json.load(open(f))['picks']:
        items.append(dict(day=day,p=pk['p'],t=pk['t'],s=pk['s'],l=pk['l'],u=pk['u'],o=pk.get('o') or pk['u']))
# dedupe
seen=set(); its=[]
for x in items:
    k=(x['day'],nk(x['p']),x['s'])
    if k in seen: continue
    seen.add(k); its.append(x)
# team game logs for pace / allowances
tgame=collections.defaultdict(dict)   # team -> g -> pts
for r in rows:
    d=tgame[r['team']].setdefault(r['g'],{'pts':0,'day':r['day'],'opp':r['opp']}); d['pts']+=r['P']
def team_avg(team,day,what='pts'):
    v=[d['pts'] for g,d in tgame[team].items() if d['day']<day]
    return stt.mean(v) if v else None
def opp_allowed(team,day):
    v=[tgame[d['opp']][g]['pts'] for g,d in tgame[team].items() if d['day']<day and g in tgame[d['opp']]]
    return stt.mean(v) if v else None
# positional allowances before day
def pos_allow(day):
    al=collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda:[0,0,0])))
    for r in rows:
        if r['day']>=day or r['pos']=='?': continue
        a=al[r['opp']][r['g']][r['pos']]; a[0]+=r['P']; a[1]+=r['S']; a[2]+=r['A']
    lg={}
    for pos in 'GFC':
        vals=[al[t][g][pos] for t in al for g in al[t]]
        lg[pos]=[stt.mean(v[i] for v in vals) if vals else 1 for i in range(3)]
    return al,lg
PA={}
out=[]
for x in its:
    k=find(x['p'])
    if not k: continue
    g=[r for r in byk[k] if r['day']<x['day']]; today=[r for r in byk[k] if r['day']==x['day']]
    if not today: continue   # DNP or no game -> void
    act=today[0][x['s']]; hit=1 if act<x['l'] else 0
    if len(g)<2: continue
    team=today[0]['team']; opp=today[0]['opp']; pos=today[0]['pos']
    if x['day'] not in PA: PA[x['day']]=pos_allow(x['day'])
    al,lg=PA[x['day']]; ix={'P':0,'S':1,'A':2}[x['s']]
    gs=al.get(opp,{}); n=len(gs)
    of=1.0
    if n and pos in 'GFC': of=1+((stt.mean(gs[gg][pos][ix] for gg in gs)/lg[pos][ix])-1)*n/(n+6)
    mins=[r['min'] for r in g]; pm=stt.mean(mins); last=g[-3:]
    cv=stt.pstdev(mins)/pm if len(g)>=3 and pm>0 else None
    tot=sum(r[x['s']] for r in g); rate=tot/sum(mins); rate3=sum(r[x['s']] for r in last)/max(1,sum(r['min'] for r in last))
    m3=stt.mean(r['min'] for r in last)
    st=sum(r['st'] for r in g)/len(g)
    ta=team_avg(team,x['day']); oa=opp_allowed(opp,x['day']); lgp=stt.mean([team_avg(t,x['day']) for t in tgame if team_avg(t,x['day'])])
    exp_team=(ta+oa)/2 if ta and oa else None
    # strength: net rating proxy
    def net(t): 
        a=team_avg(t,x['day']); b=opp_allowed(t,x['day']); return (a-b) if a and b else 0
    spread=net(team)-net(opp)
    fair=(1/x['u'])/((1/x['u'])+(1/x['o']))
    gtot=sum(d['pts'] for gg,d in [(today[0]['g'],tgame[team][today[0]['g']])])+tgame[opp][today[0]['g']]['pts']
    out.append(dict(day=x['day'],p=x['p'],team=team,opp=opp,pos=pos,s=x['s'],l=x['l'],u=x['u'],fair=fair,hit=hit,act=act,min_act=today[0]['min'],
        pm=pm,m3=m3,cv=cv,st=st,n=len(g),avg=tot/len(g),rate=rate,rate3=rate3,of=of,exp_team=exp_team,lgp=lgp,spread=spread,
        under3=sum(1 for r in last if r[x['s']]<x['l']),gtot=gtot))
json.dump(out,open('ds_all.json','w'))
print(len(out), collections.Counter(o['day'] for o in out))
