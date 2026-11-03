import re,json,time,collections
P=json.load(open('/home/claude/r8/sel8.json')); tk=json.load(open('/home/claude/r8/plan8b.json'))['tk']
order=sorted(range(len(tk)),key=lambda k:(len(tk[k]),k))
stake=lambda n:100 if n==8 else 50
def legs(t,full):
    L=sorted(t,key=lambda i:(P[i]['time'],P[i]['g'],P[i]['t'],P[i]['p']))
    out=[]
    for i in L:
        x=P[i]; d={'c':x['c'],'p':x['p'],'t':x['t'],'s':x['s'],'l':x['l'],'u':x['u']}
        if full: d.update({'pr':round(x['pr'],3),'fa':x['fair'],'sc':round(x['pr']*x['u']-1,3),'g':x['g'],'st':False,'f':False})
        out.append(d)
    return out
plan={'v':1,'round':'8','tickets':[{'stake':stake(len(tk[k])),'legs':legs(tk[k],False)} for k in order]}
open('/mnt/user-data/outputs/plan_42_27okt.txt','w').write(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open('/home/claude/r8/p8.html').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
cp={'id':'cp-r8d1-42','label':'Kolo 8, 27.10: 30 osmica po 100, 10 desetki i 2 dvanaestice po 50 din (3.600 din)',
    'desc':'Nova procena sa kontekstom utakmice (v6). 39 igrača, 67 parova sa šansom od 56% naviše i kvotom od 1,70; par najviše na 9 od 42 tiketa (21%), igrač najviše na 11; ★ bez dodatnih ponavljanja. Uglavnom spori mečevi: Panatinaikos – Milano, Zvezda – Makabi, Valensija – Fener, Bajern – Barsa; iz Dubai – Pariz samo Kabengele (4 tiketa), iz Baskonija – Real 3 para.',
    'stats':{'app':0.474,'market':0.096},'at':'2026-10-27T09:10:00Z','round':'8',
    'tickets':[{'stake':stake(len(tk[k])),'stack':'','stackLbl':'','legs':legs(tk[k],True)} for k in order]}
st['claudePlans']=[p for p in st['claudePlans'] if p['id']!=cp['id']]+[cp]
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open('/home/claude/r8/p8final.html','w').write(h)
print('ok', len(plan['tickets']), sum(t['stake'] for t in plan['tickets']))
