import re,json,time
P=json.load(open('/home/claude/r8/sel8c.json')); tk=json.load(open('/home/claude/r8/plan8e.json'))['tk'][42:]
order=sorted(range(len(tk)),key=lambda k:(len(tk[k]),k))
stake=lambda n:35 if n==8 else 50
def legs(t,full):
    out=[]
    for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['g'],P[i]['t'],P[i]['p'])):
        x=P[i]; d={'c':x['c'],'p':x['p'],'t':x['t'],'s':x['s'],'l':x['l'],'u':x['u']}
        if full: d.update({'pr':round(x['pr'],3),'fa':x['fair'],'sc':round(x['pr']*x['u']-1,3),'g':x['g'],'st':False,'f':False})
        out.append(d)
    return out
plan={'v':1,'round':'8','tickets':[{'stake':stake(len(tk[k])),'legs':legs(tk[k],False)} for k in order]}
open('/mnt/user-data/outputs/plan_50_dodatak_27okt.txt','w').write(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
cp={'id':'cp-r8d1-50','label':'Kolo 8, 27.10, dodatak: 32 desetke i 17 dvanaestica po 50 din i jedna osmica od 35 din (2.485 din)',
    'desc':'Dodatak uz plan od 42 tiketa (ukupno 92 tiketa, 6.085 din iz dobitka). 45 igrača u oba plana zajedno, 6 novih: Brizuela, Hayes-Davis, Badio, Grant, Melli, Cole. Igrač najviše na 24 od 92 tiketa (26%), par najviše na 20. Najviše iz Panatinaikos – Milano i Valensija – Fener.',
    'stats':{'app':0.54,'market':0.116},'at':'2026-10-27T09:05:00Z','round':'8',
    'tickets':[{'stake':stake(len(tk[k])),'stack':'','stackLbl':'','legs':legs(tk[k],True)} for k in order]}
st['claudePlans']=[p for p in st['claudePlans'] if p['id']!=cp['id']]+[cp]
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h)
print('ok',len(plan['tickets']),sum(t['stake'] for t in plan['tickets']))
