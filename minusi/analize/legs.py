import json,re,unicodedata,collections,statistics as stt
st=json.load(open('/home/claude/app/v6/state_now.json'))
rows=json.load(open('/home/claude/form/rows.json'))
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
    if len(c)==1: return c[0]
    c=[kk for kk in keys if kk.split()[-1]==t[-1]]
    return c[0] if len(c)==1 else None
games=collections.defaultdict(list)  # team -> [(day,g,opp)]
seen=set()
for r in rows:
    if (r['team'],r['g']) in seen: continue
    seen.add((r['team'],r['g'])); games[r['team']].append((r['day'],r['g'],r['opp']))
for t in games: games[t].sort()
res=st['results']
def key(t,l):
    ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
    return '|'.join([str(t['round']).strip(),l['p'].strip().lower(),l['stat'],ls])
unk=collections.Counter(); out=[]
for t in st['tickets']:
    for i,l in enumerate(t['legs']):
        code=TM.get(l['team'].strip())
        if not code: unk[l['team']]+=1
        g=None; gd=None; opp=None
        if code:
            nxt=[x for x in games[code] if x[0]>=t['date']]
            if nxt: gd,g,opp=nxt[0]
        r=res.get(key(t,l)); k=find(l['p'])
        prior=[x for x in byk.get(k,[]) if gd and x['day']<gd and x['min']>0] if k else []
        pm=stt.mean(x['min'] for x in prior) if prior else None
        stv=sum(x['st'] for x in prior)/len(prior) if prior else None
        pos=collections.Counter(x['pos'] for x in byk[k]).most_common(1)[0][0] if k else None
        act_min=None
        if k and g:
            tr=[x for x in byk[k] if x['g']==g]
            act_min=tr[0]['min'] if tr else 0
        stt_='pend' if not r else 'void' if r.get('dnp') else 'hit' if r['actual']<l['line'] else 'miss'
        out.append(dict(tid=t['id'],date=t['date'],round=str(t['round']),stake=t['stake'],n=len(t['legs']),win_bonus=t.get('bonus'),refund=t.get('refund'),
            p=l['p'],team=l['team'],code=code,stat=l['stat'],line=l['line'],odds=l['odds'],sc=l.get('sc'),res=stt_,act=(r or {}).get('actual'),
            g=g,gday=gd,opp=opp,pm=pm,stv=stv,nprior=len(prior),pos=pos,act_min=act_min))
json.dump(out,open('legs.json','w'))
print(len(out),collections.Counter(o['res'] for o in out),'unk teams',unk)
print('bez utakmice',sum(1 for o in out if o['g'] is None),'bez pm',sum(1 for o in out if o['pm'] is None))
print(collections.Counter((o['date'],o['gday']) for o in out))
