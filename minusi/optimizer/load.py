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
if a.povrede: st['injuries']=json.load(open(a.povrede,encoding='utf8'))
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(a.izlaz,'w',encoding='utf8').write(h)
print('ok, parova u ponudi:',len(off['picks']),'| ponuda od',off['at'],'| kvote od',st['lines']['at'],'| povrede kolo',st['injuries']['round'],st['injuries']['at'])
