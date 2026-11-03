import re,json,time,sys
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
OUT=sys.argv[1]
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
off=json.load(open('/home/claude/r8/offer_raw.json'))
st['offer']=off
snaps=st.get('offerSnaps') or []
if not any(s.get('at')==off['at'] for s in snaps): snaps.append({'at':off['at'],'picks':off['picks']})
st['offerSnaps']=snaps[-10:]
CODE={'Dubai':'DUB','Paris':'PRS','Bayern Munich':'MUN','Barcelona':'BAR','Crvena Zvezda':'RED','Maccabi Tel Aviv':'TEL','Panathinaikos':'PAN','Armani Milano':'MIL','Valencia':'PAM','Fenerbahce':'ULK','Baskonia':'BAS','Real Madrid':'MAD','Besiktas':'BES','Olympiacos':'OLY','Hapoel Tel Aviv':'HTA','Anadolu Efes':'IST','Asvel':'ASV','Partizan':'PAR','Virtus Bologna':'VIR','Zalgiris Kaunas':'ZAL'}
A=[("Dubai","Paris",1.2,4.8,179.5,95.5,84.5),("Bayern Munich","Barcelona",1.91,1.94,176.5,88.5,88.5),("Crvena Zvezda","Maccabi Tel Aviv",1.46,3,172.5,88.5,83.5),("Panathinaikos","Armani Milano",1.11,7,165.5,89.5,75.5),("Valencia","Fenerbahce",1.95,1.9,175.5,87.5,87.5),("Baskonia","Real Madrid",4.4,1.23,182.5,86.5,96.5),
   ("Besiktas","Olympiacos",3.2,1.38,175.5,84.5,90.5),("Hapoel Tel Aviv","Anadolu Efes",1.34,3.45,172.5,89.5,83.5),("Asvel","Partizan",1.86,1.99,168.5,84.5,84.5),("Virtus Bologna","Zalgiris Kaunas",2.07,1.8,171.5,85.5,86.5)]
st['lines']={'at':'2026-10-27T08:28:24.398Z','src':'AdmiralBet, kvote utakmica 27.10. u 9:28','games':{CODE[a]+'-'+CODE[b]:{'total':t,'hTot':ht,'aTot':at,'ml1':m1,'ml2':m2} for a,b,m1,m2,t,ht,at in A}}
INJ=[('Justin Anderson','Dubai','out','zadnja loža'),('Mam Jaiteh','Dubai','out','Ahilova tetiva'),('Dzanan Musa','Dubai','out','nije igrao ove sezone'),
 ('Nadir Hifi','Paris','dtd','skočni zglob, nada se povratku'),('Frank Ntilikina','Paris','dtd','nada se povratku'),
 ('Iffe Lundberg','Maccabi Tel Aviv','out','kvadriceps, 6 do 8 nedelja'),('Yoan Makoundou','Barcelona','out','koleno'),
 ('Nikos Rogkavopoulos','Panathinaikos','doubtful','zadnja loža, upitan'),('Nate Reuvers','Valencia','out','kost stopala'),
 ('Usman Garuba','Real Madrid','out','Ahilova tetiva'),('Gabriel Deck','Real Madrid','out','rame, posle operacije')]
st['injuries']={'round':'8','at':'27.10.2026. 9:30','src':'Eurodevotion, izveštaj o povredama za 27. oktobar; Eurohoops (Reuvers, 25.10.)','list':[{'p':a,'t':b,'s':c,'note':d} for a,b,c,d in INJ]}
st['savedAt']=int(time.time()*1000)
json.dump(st,open('/home/claude/r8/state8.json','w'))
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(OUT,'w').write(h); print('ok',len(off['picks']))
