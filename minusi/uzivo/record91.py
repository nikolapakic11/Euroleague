import re,json,time,collections
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
rows=json.load(open('/home/claude/form/rows.json'))
R=collections.defaultdict(list)
for r in sorted(rows,key=lambda r:(r['d'],r['g'])):
    if r['min']>0: R[r['k']].append(round(r['min'],1))
M=st['minLog']['m']
for k in list(M):
    if k in R: M[k]=R[k]
for k,v in R.items():
    if k not in M and not (k=='oshae brissett' and 'oshae j brissett' in M): M[k]=v
if 'oshae brissett' in R and 'oshae j brissett' in M: M['oshae j brissett']=R['oshae brissett']
st['minLog']['at']='2026-11-04'
st['ctx2']=json.load(open('/home/claude/r10a/ctx2_new.json'))
st['lineStats']=json.load(open('/home/claude/lines/linestats.json'))
note=('Kolo 10, 4.11.2026: odigrana samo utakmica Real – Panatinaikos 112:115 posle produžetka; Nikola nije igrao minuse. Cela Admiralova ponuda za tu utakmicu: minusi 15 od 33 (poeni 6 od 16, skokovi 7 od 12, asistencije 2 od 5), visok rezultat zbog produžetka (Nunn 33, Feliz 27, Abalde 23). '
      'Zapisnik 91 ubačen u bazu; minLog, ctx2 i tabela tačnih granica (sada 1.770 minusa iz ponude, 8.10. do 4.11.) osveženi.')
if note not in st['notes']['text']: st['notes']['text'].append(note)
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok')
