import re,json,time,collections
exec(open('/home/claude/live29/status.py').read().split("for g,i in GINFO.items()")[0])
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st_=json.loads(pat.search(h).group(2))
plan=json.load(open('/mnt/user-data/outputs/plan_40_29okt.txt'))['tickets']
new=[{'id':'r9d1-%02d'%(k+1),'date':'2026-10-29','round':'9','stake':100,'fund':'dobitak' if k<18 else 'novi','legs':[{'p':l['p'],'team':l['t'],'stat':l['s'],'line':l['l'],'odds':l['u']} for l in t['legs']]} for k,t in enumerate(plan)]
for t in new:
    if t['id']=='r9d1-12': t['refund']=200
st_['tickets']=[t for t in st_['tickets'] if not t['id'].startswith('r9d1-')]+new
for t in new:
    for l in t['legs']:
        ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
        k='|'.join(['9',l['p'].strip().lower(),l['stat'],ls]); b=find(l['p'])
        st_['results'][k]={'actual':None,'dnp':True} if (not b or b['min'] in ('DNP','',None,'00:00')) else {'actual':b[l['stat']],'dnp':False,'min':b['min']}
rows=json.load(open('/home/claude/form/rows.json'))
R=collections.defaultdict(list)
for r in sorted(rows,key=lambda r:(r['d'],r['g'])):
    if r['min']>0: R[r['k']].append(round(r['min'],1))
M=st_['minLog']['m']
for k in list(M):
    if k in R: M[k]=R[k]
for k,v in R.items():
    if k not in M and not (k=='oshae brissett' and 'oshae j brissett' in M): M[k]=v
if 'oshae brissett' in R and 'oshae j brissett' in M: M['oshae j brissett']=R['oshae brissett']
st_['minLog']['at']='2026-10-29'; st_['ctx2']=json.load(open('/home/claude/r9/ctx2_new.json'))
n=('Kolo 9, 29.10.2026: upisano 40 osmica po 100 po planu cp-r9d1-40 (pretpostavka da je odigran plan bez izmena; 2.200 svežeg novca i 1.800 od povraćaja). Bez dobitnog tiketa; jedan promašaj samo na r9d1-12 (Moneke P), očekivani povraćaj 200 (kvota ostalih 60,3, x2), upisano 200 dok Nikola ne potvrdi. '
   'Najgori dan sezone za minuse: cela ponuda 42% (plusevi 58%), najbolja četvrtina po v6 48%. Parovi na tiketima 46%; lista 20 najboljih 10 od 19; plus predlozi 6 od 7 (Jessup i Izundu nisu igrali). '
   'Tikete oborili Clyburn P (21, 16 tiketa), Alize Johnson S (8, 16), Tavares P (14, 16), Horton-Tucker S (5, 14), Hifi P (26, 12), Moneke S, Campazzo A, Melli S (po 11). Rezultati: Zvezda – Bajern 103:73, Makabi – Pariz 94:99, Real – Fener 95:76. minLog i ctx2 osveženi sa utakmicama 81 do 83.')
if n not in st_['notes']['text']: st_['notes']['text'].append(n)
st_['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st_,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok',len(new))
