import re,json,time,collections,math
exec(open('/home/claude/live30/status.py').read().split("for g,i in GINFO.items()")[0])
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st_=json.loads(pat.search(h).group(2))
n=0
for t in st_['tickets']:
    if not t['id'].startswith('r9d2'): continue
    for l in t['legs']:
        ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
        k='|'.join(['9',l['p'].strip().lower(),l['stat'],ls]); b=find(l['p'])
        st_['results'][k]={'actual':None,'dnp':True} if (not b or b['min'] in ('DNP','',None,'00:00')) else {'actual':b[l['stat']],'dnp':False,'min':b['min']}
        n+=1
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
st_['minLog']['at']='2026-10-30'; st_['ctx2']=json.load(open('/home/claude/live30/ctx2_new.json'))
note=('Kolo 9, 30.10.2026: 90 minus tiketa (7.000 svežeg novca, plan cp-r9d2-90) + 10 tiketa r9d2-g (500, plusevi greškom uplaćeni kao minusi). '
 'Dobitna jedna osmica r9d2-22 (kvota 130,5, isplata sa bonusom 16% oko 15.138). Nijedan tiket sa tačno jednim promašajem, pa bez povraćaja (čeka potvrdu). Svi g tiketi pali; da su uplaćeni kao plusevi, ni jedan ne bi prošao (najbolji 5 od 6). '
 'Jedinstveni parovi na tiketima 41 od 81 (51%), Balcerowski P nije igrao. Tikete oborili Okobo S (3, 24 tiketa), Carsen Edwards A (4, 24), Osetkowski A1,5 (2, 24), Micić P (15, 24), Diarra S (7, 24), Frazier P (15, 24), Moore P (13, 24), Valančiunas P (16, 19), Punter P (18, 18), Lesor S (11, 16), Santos S (5, 16). '
 'Lista 15 minusa 9 od 15; lista 10 pluseva 5 od 10; 12 plus predloga 7 od 12. Free bet mix i dve mix osmice pale. Rezultati: Dubai – Hapoel 97:83, ASVEL – Baskonija 94:79, Žalgiris – Partizan 87:80, Barselona – Valensija 98:94, Efes – Panatinaikos 83:68, Virtus – Bešiktaš 101:103, Olimpijakos – Milano 84:78. minLog i ctx2 osveženi sa utakmicama 84 do 90.')
if note not in st_['notes']['text']: st_['notes']['text'].append(note)
st_['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st_,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok',n)
