"""Upisuje rezultate odigranih tiketa jednog kola/dana u stanje aplikacije (results, minLog, ctx2, napomena).
Upotreba: python3 -I upis_rezultata.py --kolo 10 --prefiks r10d2- --datum 2026-11-05 --utakmice 92,93,94,95,96 [--napomena fajl.txt]
Čita zapisnike iz baza/zapisnici, piše stanje u minusi/aplikacija/evroliga-minusi.html i stanje.json (rezervna kopija).
Igrač koji nije u zapisniku utakmice svog tima ili ima DNP upisuje se kao 'dnp' (par se vraća). Povraćaji (iznos sa PDF-a) se ne upisuju ovde."""
import re,json,time,collections,sys,os,argparse,unicodedata
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import BAZA,APP_HTML,MINUSI
ap=argparse.ArgumentParser(); ap.add_argument('--kolo',required=True); ap.add_argument('--prefiks',required=True); ap.add_argument('--datum',required=True)
ap.add_argument('--utakmice',required=True); ap.add_argument('--napomena'); a=ap.parse_args()
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r"[.']",'',t); t=re.sub(r'-',' ',t); t=re.sub(r'[^a-z ]','',t); return ' '.join(w for w in t.split() if w not in SUF)
BOX={}
for g in map(int,a.utakmice.split(',')):
    d=json.load(open(f'{BAZA}/zapisnici/{g}.json'))
    for s in d['Stats']:
        for p in s['PlayersStats']:
            x=p['Player'].split(','); BOX[nk((x[1] if len(x)>1 else '')+' '+x[0])]=dict(g=g,P=p['Points'],S=p['TotalRebounds'],A=p['Assistances'],min=p['Minutes'])
keys=list(BOX)
def find(name):
    k=nk(name)
    if k in BOX: return BOX[k]
    t=k.split(); c=[kk for kk in keys if kk.split()[-1]==t[-1] and kk.split()[0][:3]==t[0][:3]]
    return BOX[c[0]] if len(c)==1 else None
h=open(APP_HTML,encoding='utf8').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
n=0; stat=collections.Counter()
for t in st['tickets']:
    if not t['id'].startswith(a.prefiks): continue
    for l in t['legs']:
        ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
        k='|'.join([a.kolo,l['p'].strip().lower(),l['stat'],ls]); b=find(l['p'])
        st['results'][k]={'actual':None,'dnp':True} if (not b or b['min'] in ('DNP','',None,'00:00')) else {'actual':b[l['stat']],'dnp':False,'min':b['min']}
        n+=1
rows=json.load(open(BAZA+'/rows.json'))
R=collections.defaultdict(list)
for r in sorted(rows,key=lambda r:(r['d'],r['g'])):
    if r['min']>0: R[r['k']].append(round(r['min'],1))
M=st['minLog']['m']
for k in list(M):
    if k in R: M[k]=R[k]
for k,v in R.items():
    if k not in M and not (k=='oshae brissett' and 'oshae j brissett' in M): M[k]=v
if 'oshae brissett' in R and 'oshae j brissett' in M: M['oshae j brissett']=R['oshae brissett']
st['minLog']['at']=a.datum; st['ctx2']=json.load(open(BAZA+'/ctx2.json'))
if a.napomena:
    note=open(a.napomena,encoding='utf8').read().strip()
    if note not in st['notes']['text']: st['notes']['text'].append(note)
st['savedAt']=int(time.time()*1000)
js=json.dumps(st,ensure_ascii=False,separators=(',',':'))
open(APP_HTML,'w',encoding='utf8').write(pat.sub(lambda m:m.group(1)+js.replace('<','\\u003c')+m.group(3),h,count=1))
open(MINUSI+'/aplikacija/stanje.json','w',encoding='utf8').write(json.dumps(st,ensure_ascii=False,indent=0))  # isti format kao ranije
print('ok, upisano parova:',n,'| rezultata u stanju:',len(st['results']))
