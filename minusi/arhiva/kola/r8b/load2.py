import re,json,time,sys
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
# povracaji 27.10: ukupno 1.100 na 4 tiketa
for t in []:
    if t['id'] in ('r8d1-05','r8d1-16','r8d1-25','r8d1-29'): t['refund']=275
n="27.10.2026: povraćaj za 4 osmice sa jednim promašajem (r8d1-05, r8d1-16, r8d1-25, r8d1-29) ukupno 1.100 din, upisano po 275 jer pojedinačni iznosi nisu poznati. Stanje na računu posle kola 8 (27.10): 1.100 din; Nikola dopunjuje po potrebi."
if n not in st['notes']['text']: st['notes']['text'].append(n)
off=json.load(open('/home/claude/r8b/offer2.json'))
st['offer']=off
snaps=st.get('offerSnaps') or []
if not any(s.get('at')==off['at'] for s in snaps): snaps.append({'at':off['at'],'picks':off['picks']})
st['offerSnaps']=snaps[-10:]
CODE={'Besiktas':'BES','Olympiacos':'OLY','Hapoel Tel Aviv':'HTA','Anadolu Efes':'IST','Asvel':'ASV','Partizan':'PAR','Virtus Bologna':'VIR','Zalgiris Kaunas':'ZAL','Crvena Zvezda':'RED','Bayern Munich':'MUN','Maccabi Tel Aviv':'TEL','Paris':'PRS','Real Madrid':'MAD','Fenerbahce':'ULK','Barcelona':'BAR','Valencia':'PAM'}
A=[("Besiktas","Olympiacos",2.12,1.73,171.5,84.5,86.5),("Hapoel Tel Aviv","Anadolu Efes",1.39,3.05,172.5,88.5,83.5),("Asvel","Partizan",1.88,1.93,168.5,84.5,84.5),("Virtus Bologna","Zalgiris Kaunas",1.82,2,173.5,86.5,86.5),
   ("Crvena Zvezda","Bayern Munich",1.29,3.65,164.5,86.5,78.5),("Maccabi Tel Aviv","Paris",1.46,2.75,182.5,93.5,88.5),("Real Madrid","Fenerbahce",1.59,2.37,171.5,87.5,84.5),("Barcelona","Valencia",1.8,2.02,182.5,91.5,90.5)]
st['lines']={'at':'2026-10-28T10:24:25.140Z','src':'AdmiralBet, kvote utakmica 28.10. u 11:24','games':{CODE[a]+'-'+CODE[b]:{'total':t,'hTot':ht,'aTot':at,'ml1':m1,'ml2':m2} for a,b,m1,m2,t,ht,at in A}}
INJ=[('Nikola Milutinov','Olympiacos','out','nožni prst, izostavljen iz sastava'),('Jean Montero','Olympiacos','out','skočni zglob'),('Evan Fournier','Olympiacos','out','ne igra'),('Tyler Dorsey','Olympiacos','out','ne igra'),
 ('DaQuan Jeffries','Besiktas','out','zglob šake, operacija'),('Lonnie Walker','Besiktas','dtd','povreda u turskom prvenstvu, neizvesno'),
 ('Nigel Williams-Goss','Zalgiris Kaunas','out','zadnja loža, do 4 nedelje'),
 ('Mike James','Anadolu Efes','out','Ahilova tetiva'),('PJ Dozier','Anadolu Efes','out','leđa'),('Isaia Cordinier','Anadolu Efes','out','oporavak posle operacije'),('Georgios Papagiannis','Anadolu Efes','out','koleno'),
 ('Tonye Jekiri','Partizan','out','prepona'),('Vanja Marinkovic','Partizan','out','Ahilova tetiva'),('Mathis Dossou-Yovo','Lyon-Villeurbanne','out','prepona')]
st['injuries']={'round':'8','at':'28.10.2026. 11:30','src':'Eurohoops (Olimpijakos i Bešiktaš, 27.10.), RotoWire (Williams-Goss, Jeffries), izveštaj za 7. kolo (Efes, Partizan, Asvel)','list':[{'p':a,'t':b,'s':c,'note':d} for a,b,c,d in INJ]}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(sys.argv[1],'w').write(h); print('ok',len(off['picks']))
