import re,json,time,collections,math
P=json.load(open('/home/claude/r8/sel8f.json')); tk=json.load(open('/home/claude/r8/plan8g.json'))['tk']
cfg=json.load(open('/home/claude/r8/cfgg.json')); sizes=cfg['sizes']
stakes=[100]*5+[100]*25+[50]*42+[50]*19+[35]
assert len(stakes)==len(tk)==92 and all(len(t)==s for t,s in zip(tk,sizes))
def legs(t,full):
    out=[]
    for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['g'],P[i]['t'],P[i]['p'])):
        x=P[i]; d={'c':x['c'],'p':x['p'],'t':x['t'],'s':x['s'],'l':x['l'],'u':x['u']}
        if full: d.update({'pr':round(x['pr'],3),'fa':x['fair'],'sc':round(x['pr']*x['u']-1,3),'g':x['g'],'st':False,'f':False})
        out.append(d)
    return out
rest=list(range(5,92)); order=[k for k in rest if len(tk[k])==8 and stakes[k]==100]+[k for k in rest if stakes[k]==35]+[k for k in rest if len(tk[k])==10]+[k for k in rest if len(tk[k])==12]
plan={'v':1,'round':'8','tickets':[{'stake':stakes[k],'legs':legs(tk[k],False)} for k in order]}
open('/mnt/user-data/outputs/plan_87_ostatak_27okt.txt','w').write(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
print('ostatak',len(plan['tickets']),sum(t['stake'] for t in plan['tickets']),collections.Counter((len(t['legs']),t['stake']) for t in plan['tickets']))
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open('/home/claude/r8/p8b.html').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
cp={'id':'cp-r8d1-92','label':'Kolo 8, 27.10: objedinjeni plan, 92 tiketa za 6.085 din (prvih 5 osmica već odigrano)',
    'desc':'Ponuda u 10:12: Joel Parra skinut iz ponude, računa se kao odsutan, pa su Tyrese Martin (oslabljena pozicija) i Justin Robinson izbačeni iz novih tiketa; ostali iz Barselone sa nešto nižom šansom. Prvih 5 osmica po 100 je odigrano iz jutarnjeg plana; ostatak: 25 osmica po 100, jedna osmica od 35, 42 desetke i 19 dvanaestica po 50 din. 43 igrača, igrač najviše na 24 od 92 tiketa (26%), par najviše na 20.',
    'stats':{'app':0.49,'market':0.103},'at':'2026-10-27T09:40:00Z','round':'8',
    'tickets':[{'stake':stakes[k],'stack':'','stackLbl':'','legs':legs(tk[k],True)} for k in list(range(5))+order]}
st['claudePlans']=[p for p in st['claudePlans'] if p['id'] not in ('cp-r8d1-42','cp-r8d1-50','cp-r8d1-92')]+[cp]
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('app ok')
# summary
new=[tk[k] for k in order]
c=collections.Counter(P[i]['g'] for t in new for i in t); print(c)
bar=collections.Counter((P[i]['p'],P[i]['s']) for t in new for i in t if P[i]['t']=='Barcelona'); print('Barsa u novim:',bar)
print('prosecna sansa (novi)',round(sum(P[i]['pr'] for t in new for i in t)/sum(len(t) for t in new),3))
