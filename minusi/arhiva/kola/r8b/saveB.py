import re,json,time
P=json.load(open('/home/claude/r8b/sel_B.json')); tk=json.load(open('/home/claude/r8b/plan_B.json'))['tk']
def legs(t,full):
    out=[]
    for i in sorted(t,key=lambda i:(P[i]['time'],P[i]['g'],P[i]['t'],P[i]['p'])):
        x=P[i]; d={'c':x['c'],'p':x['p'],'t':x['t'],'s':x['s'],'l':x['l'],'u':x['u']}
        if full: d.update({'pr':round(x['pr'],3),'fa':x['fair'],'sc':round(x['pr']*x['u']-1,3),'g':x['g'],'st':False,'f':False})
        out.append(d)
    return out
plan={'v':1,'round':'8','tickets':[{'stake':50,'legs':legs(t,False)} for t in tk]}
open('/mnt/user-data/outputs/plan_30_28okt.txt','w').write(json.dumps(plan,ensure_ascii=False,separators=(',',':')))
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open('/home/claude/r8b/p.html').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
cp={'id':'cp-r8d2-30','label':'Kolo 8, 28.10: 30 osmica po 50 din (1.500 din)',
    'desc':'4 utakmice. Po pouci od 27.10: samo najjači parovi (šansa od 58% naviše), 25 igrača, 37 parova, bez dopunjavanja slabijim parovima; zato više ponavljanja: igrač najviše na 11 od 30 tiketa, par najviše na 10. Najviše iz Virtus – Žalgiris (bez Williams-Gossa; Keenan Evans nije u ponudi).',
    'stats':{'app':0.403,'market':0.103},'at':'2026-10-28T10:45:00Z','round':'8',
    'tickets':[{'stake':50,'stack':'','stackLbl':'','legs':legs(t,True)} for t in tk]}
st['claudePlans']=[p for p in st['claudePlans'] if p['id']!=cp['id']]+[cp]
n=('Pouka 27.10. (Nikola se složio): ako kladionica tokom dana skine igrača iz ponude, računati da verovatno ne igra i blago preračunati plan (saigrači na istoj poziciji dobijaju više minuta). '
   'Sa malo utakmica ne širiti plan na slabije parove radi manjeg ponavljanja: na 27.10. parovi sa liste 20 najboljih prošli 65%, ostali 48%.')
if n not in st['notes']['text']: st['notes']['text'].append(n)
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok',len(plan['tickets']),sum(t['stake'] for t in plan['tickets']))
