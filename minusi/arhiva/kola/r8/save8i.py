import re,json,time,collections
P=json.load(open('/home/claude/r8/sel8h.json')); tk=json.load(open('/home/claude/r8/plan8i.json'))['tk']
new=tk[55:]
def legs(t,full):
    out=[]
    for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['g'],P[i]['t'],P[i]['p'])):
        x=P[i]; d={'c':x['c'],'p':x['p'],'t':x['t'],'s':x['s'],'l':x['l'],'u':x['u']}
        if full: d.update({'pr':round(x['pr'],3),'fa':x['fair'],'sc':round(x['pr']*x['u']-1,3),'g':x['g'],'st':False,'f':False})
        out.append(d)
    return out
order=[k for k in range(len(new)) if len(new[k])==10]+[k for k in range(len(new)) if len(new[k])==12]
plan={'v':1,'round':'8','tickets':[{'stake':50,'legs':legs(new[k],False)} for k in order]}
open('/mnt/user-data/outputs/plan_37_ostatak_27okt.txt','w').write(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
o=json.load(open('/home/claude/r8/offer3_raw.json')); codes={(p['c'],p['s'],p['l']) for p in o['picks']}
bad=[(l['p'],l['s']) for t in plan['tickets'] for l in t['legs'] if (l['c'],l['s'],l['l']) not in codes]
print('ostatak',len(plan['tickets']),sum(t['stake'] for t in plan['tickets']),collections.Counter(len(t['legs']) for t in plan['tickets']),'van ponude',bad)
cnt=collections.Counter(P[i]['p'] for t in new for i in t); print('najvise u novih 37:',cnt.most_common(8))
print('Barsa u novih 37:',collections.Counter((P[i]['p'],P[i]['s']) for t in new for i in t if P[i]['t']=='Barcelona'))
print('prosecna sansa (novi)',round(sum(P[i]['pr'] for t in new for i in t)/sum(len(t) for t in new),3),'igraca',len(cnt))
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open('/home/claude/r8/p8c.html').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
old=[p for p in st['claudePlans'] if p['id']=='cp-r8d1-92'][0]
played=old['tickets'][:55]
cp={'id':'cp-r8d1-92','label':'Kolo 8, 27.10: objedinjeni plan, 92 tiketa za 6.085 din (55 odigrano, ostatak 37 po 50 din)',
    'desc':'55 tiketa odigrano (5 osmica iz jutarnjeg plana i 50 iz plana od 87). U 11:10 Alec Peters skinut iz ponude; izveštaj o povredama (Eurodevotion, 27.10. 7:00) kaže da Milano ima sve igrače i ne pominje ni Parru, pa se ni Peters ni Parra ne računaju kao odsutni. Tyrese Martin i dalje van novih tiketa jer je kladionica podigla njegove granice. Ostatak: 18 desetki i 19 dvanaestica po 50 din; igrač najviše na 24 od 92 i najviše na 15 od 37 novih.',
    'stats':{'app':0.496,'market':0.105},'at':'2026-10-27T10:20:00Z','round':'8',
    'tickets':played+[{'stake':50,'stack':'','stackLbl':'','legs':legs(new[k],True)} for k in order]}
st['claudePlans']=[p for p in st['claudePlans'] if p['id']!='cp-r8d1-92']+[cp]
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('app ok',len(cp['tickets']))
