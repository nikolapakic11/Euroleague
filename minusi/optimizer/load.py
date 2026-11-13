"""Ubacuje ponudu (i po želji kvote utakmica i povrede) u stanje aplikacije i snima NOVU kopiju aplikacije.
Upotreba: python3 load.py <izlaz.html> <ponuda.json> [--ulaz app.html] [--kvote kvote.json] [--povrede povrede.json]
 --ulaz     aplikacija iz koje se polazi (podrazumevano minusi/aplikacija/evroliga-minusi.html)
 --kvote    JSON u obliku state['lines'] ({'at','src','games':{'ULK-BAS':{total,hTot,aTot,ml1,ml2}}}); bez njega ostaju postojeće
 --povrede  JSON u obliku state['injuries'] ({'round','at','src','list':[{p,t,s,note}]}); bez njega ostaju postojeće"""
import re,json,time,sys,os,argparse
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import APP_HTML
ap=argparse.ArgumentParser(); ap.add_argument('izlaz'); ap.add_argument('ponuda')
ap.add_argument('--ulaz',default=APP_HTML); ap.add_argument('--kvote'); ap.add_argument('--povrede')
a=ap.parse_args()
assert os.path.abspath(a.izlaz)!=os.path.abspath(APP_HTML),'izlaz ne sme da bude rezervna kopija aplikacije'
h=open(a.ulaz,encoding='utf8').read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
off=json.load(open(a.ponuda,encoding='utf8'))
st['offer']={k:off[k] for k in ('v','src','at','picks') if k in off}
snaps=st.get('offerSnaps') or []
if not any(s.get('at')==off['at'] for s in snaps): snaps.append({'at':off['at'],'picks':off['picks']})
st['offerSnaps']=snaps[-10:]
if a.kvote: st['lines']=json.load(open(a.kvote,encoding='utf8'))
if a.povrede:
    pv=json.load(open(a.povrede,encoding='utf8'))
    if 'igraci' in pv:      # od 13.11.2026: prima i procene/podaci/povrede.json (format procena) i pretvara ga
        S_={'van':'out','upitan':'doubtful'}
        pv={'round':str(pv.get('kolo','')),'at':pv.get('at',''),'src':'procene/podaci/povrede.json ('+', '.join(pv.get('izvori') or [])+')',
            'list':[{'p':' '.join(w.capitalize() for w in k.split()),'t':v.get('tim'),'s':S_[v['stanje']],'note':(v.get('tekst') or '')[:200]}
                    for k,v in pv['igraci'].items() if v.get('stanje') in S_]}
    st['injuries']=pv
# od 13.11.2026: statistika timova i raspored se osvežavaju iz same ponude (pomoćnik je šalje u 'el'); ranije su ostajali
# zastareli (teamStats.cur iz 2. kola, raspored iz 3. kola) i aplikacija je računala odbranu i tempo po njima
el=off.get('el') or {}
dfn=el.get('def') or {}
ts=st.setdefault('teamStats',{})
if dfn.get('cur'): ts['cur']=dfn['cur']
if dfn.get('prev'): ts['prev']=dfn['prev']
try:
    C=json.load(open(os.path.join(os.path.dirname(APP_HTML),'..','..','baza','ctx2.json'),encoding='utf8'))
    ts.setdefault('off',{})['cur']={t:[v[2],v[0]] for t,v in C['tm'].items()}      # [utakmica, poena po utakmici]
    st['ctx2']=C
except Exception as e:
    print('ctx2 nije osvežen:',e)
if el.get('games'):
    st['sched']={'round':str((st.get('injuries') or {}).get('round','')),'games':[{'d':g['d'].rstrip('Z'),'h':g['h'],'a':g['a']} for g in el['games']],
                 'clubs':{**(st.get('sched') or {}).get('clubs',{}),**{k:{'name':v['name'],'abbr':v['abbr']} for k,v in (el.get('clubs') or {}).items()}}}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(a.izlaz,'w',encoding='utf8').write(h)
print('ok, parova u ponudi:',len(off['picks']),'| ponuda od',off['at'],'| kvote od',st['lines'].get('at'),'| povrede kolo',st['injuries'].get('round'),st['injuries'].get('at'),'| povređenih',len(st['injuries'].get('list',[])),
      '| odbrana timova',len(ts.get('cur',{})),'timova, utakmica',max((v[0] for v in ts.get('cur',{}).values()),default=0),'| raspored',len((st.get('sched') or {}).get('games',[])))
