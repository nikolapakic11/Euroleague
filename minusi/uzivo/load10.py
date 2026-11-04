import re,json,time,sys,unicodedata
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
B='/home/claude/euroleague/baza/ponude/admiral/'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
A=json.load(open(B+'2026-11-04_a.json'))
snaps=st.get('offerSnaps') or []
for f in ('2026-11-04_a.json','2026-11-04_b.json','2026-11-04_c.json'):
    o=json.load(open(B+f))
    if not any(s.get('at')==o['at'] for s in snaps): snaps.append({'at':o['at'],'picks':o['picks']})
st['offerSnaps']=snaps[-10:]
off=json.load(open(B+'2026-11-04_c.json'))
if not off.get('el'): off['el']=A['el']
st['offer']=off
# povrede kolo 10 (zvanicni izvestaj preko Eurohoops)
P=json.load(open('/home/claude/euroleague/procene/podaci/povrede.json'))
G=json.load(open('/home/claude/euroleague/baza/games.json'))['data']
NAME={}
for g in G:
    for side in ('local','road'):
        c=g[side]['club']; NAME[c['code']]=c.get('name') or c.get('editorialName')
TEAM={'MAD':'Real Madrid','PAN':'Panathinaikos'}
def title(k): return ' '.join(w.capitalize() for w in k.split())
L=[]
for k,v in P['igraci'].items():
    if v['stanje']=='igra': continue
    L.append({'p':title(k),'t':TEAM.get(v['tim'],NAME.get(v['tim'],v['tim'])),'s':'out' if v['stanje']=='van' else 'dtd','note':v.get('tekst','')[:140]})
st['injuries']={'round':'10','at':P['at'],'src':'Zvanični izveštaj Evrolige o povredama za 10. kolo (Eurohoops)','list':L}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok ponuda',len(off['picks']),'povrede',len(L),'snimci',len(st['offerSnaps']))
