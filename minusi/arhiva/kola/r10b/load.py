import re,json,time,sys,glob
H=sys.argv[1]; OFF=sys.argv[2]
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
off=json.load(open(OFF))
st['offer']=off
snaps=st.get('offerSnaps') or []
if not any(s.get('at')==off['at'] for s in snaps): snaps.append({'at':off['at'],'picks':off['picks']})
st['offerSnaps']=snaps[-10:]
# kvote utakmica iz Soccerbeta (glavni ukupan zbir i hendikep), 5.11.
G=json.load(open('/home/claude/r10b/lines.json'))
st['lines']={'at':G['at'],'src':G['src'],'games':G['games']}
# povrede, zvanicni izvestaj za kolo 10
P=json.load(open('/home/claude/euroleague/procene/podaci/povrede.json'))
NAME={v:k for k,v in off['el']['tmap'].items()}
def title(k): return ' '.join(w.capitalize() for w in k.split())
L=[]
for k,v in P['igraci'].items():
    if v['stanje']=='igra': continue
    L.append({'p':title(k),'t':NAME.get(v['tim'],v['tim']),'s':'out' if v['stanje']=='van' else 'dtd','note':v.get('tekst','')[:140]})
st['injuries']={'round':'10','at':P['at'],'src':'Zvanični izveštaj Evrolige o povredama za 10. kolo (Eurohoops)','list':L}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok ponuda',len(off['picks']),'povrede',len(L),'kvote',len(G['games']))
