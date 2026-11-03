import re,json,time,glob,collections,sys
sys.argv=['x']
exec(open('/home/claude/live27/status.py').read().split("for g,i in GINFO.items()")[0])
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st_=json.loads(pat.search(h).group(2))
TT=[t for t in st_['tickets'] if t.get('date')=='2026-10-27']
n=0; dn=0
for t in TT:
    for l in t['legs']:
        ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
        k='|'.join([str(t['round']).strip(),l['p'].strip().lower(),l['stat'],ls])
        b=find(l['p'])
        if not b or b['min'] in ('DNP','',None,'00:00'):
            st_['results'][k]={'actual':None,'dnp':True}; dn+=1
        else:
            st_['results'][k]={'actual':b[l['stat']],'dnp':False,'min':b['min']}
        n+=1
print('nogu',n,'dnp',dn)
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
st_['minLog']['at']='2026-10-27'
st_['ctx2']=json.load(open('/home/claude/r8/ctx2_new.json'))
note=('Kolo 8, 27.10.2026, rezultati upisani: 92 tiketa za 6.085 din, bez dobitnog tiketa. Jedan promašaj (povraćaj čeka iznos): r8d1-05 (Devon Hall S, Peters nije igrao, 7 važećih parova), r8d1-16 (Brooks P, Peters nije igrao, 7 važećih), r8d1-25 (Obst P), r8d1-29 (Devon Hall S). '
      'Loš dan za minuse: cela ponuda prošla 50% (sezona 57%), ukupni poeni iznad kvote u 4 od 6 utakmica (Dubai – Pariz 192, Baskonija – Real 190). Odigrani parovi 52% jedinstveni, 55% po mestima. '
      'Lista 20 najboljih (v6) prošla 13/20 (65%), početnih 10: 6/9 (Peters nije igrao); parovi sa liste 20 na tiketima 65% po mestima, ostali odigrani parovi 48%: širenje na 45 igrača radi manjeg ponavljanja oborilo je prosek. v6 na celoj ponudi: najbolja četvrtina 57% prema 50% za celu ponudu. '
      'Peters i Parra skinuti iz ponude tokom dana: obojica nisu igrali; Tyrese Martin (Parrina pozicija) 25 min, 12 poena, pa je izbacivanje Martina bilo ispravno. Kad kladionica skine igrača tokom dana, to je jak znak da ne igra. minLog i ctx2 osveženi sa utakmicama 71 do 76.')
if note not in st_['notes']['text']: st_['notes']['text'].append(note)
st_['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st_,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok')
