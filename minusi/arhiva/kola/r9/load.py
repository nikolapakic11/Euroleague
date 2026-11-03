import re,json,time,sys
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
off=json.load(open(sys.argv[2]))
st['offer']=off
snaps=st.get('offerSnaps') or []
if not any(s.get('at')==off['at'] for s in snaps): snaps.append({'at':off['at'],'picks':off['picks']})
st['offerSnaps']=snaps[-10:]
CODE={'Crvena Zvezda':'RED','Bayern Munich':'MUN','Maccabi Tel Aviv':'TEL','Paris':'PRS','Real Madrid':'MAD','Fenerbahce':'ULK','Dubai':'DUB','Hapoel Tel Aviv':'HTA','Anadolu Efes':'IST','Panathinaikos':'PAN','Zalgiris Kaunas':'ZAL','Partizan':'PAR','Asvel':'ASV','Baskonia':'BAS','Olympiacos':'OLY','Armani Milano':'MIL','Barcelona':'BAR','Valencia':'PAM','Virtus Bologna':'VIR','Besiktas':'BES'}
A=[("Crvena Zvezda","Bayern Munich",1.3,3.6,167.5,87.5,80.5),("Maccabi Tel Aviv","Paris",1.46,2.75,183.5,93.5,89.5),("Real Madrid","Fenerbahce",1.44,2.8,172.5,88.5,83.5),("Dubai","Hapoel Tel Aviv",1.57,2.42,173.5,88.5,85.5),("Anadolu Efes","Panathinaikos",2.75,1.45,164.5,80.5,84.5),("Zalgiris Kaunas","Partizan",1.3,3.55,167.5,87.5,80.5),("Asvel","Baskonia",1.53,2.5,180.5,92.5,88.5),("Olympiacos","Armani Milano",1.12,6.4,169.5,90.5,78.5),("Barcelona","Valencia",1.8,2.02,182.5,91.5,90.5),("Virtus Bologna","Besiktas",1.68,2.2,177.5,89.5,87.5)]
st['lines']={'at':'2026-10-29T09:11:35.923Z','src':'AdmiralBet, kvote utakmica 29.10. u 10:11','games':{CODE[a]+'-'+CODE[b]:{'total':t,'hTot':ht,'aTot':at,'ml1':m1,'ml2':m2} for a,b,m1,m2,t,ht,at in A}}
INJ=[('Iffe Lundberg','Maccabi Tel Aviv','out','kvadriceps'),('Frank Ntilikina','Paris','doubtful','neizvesno'),('Usman Garuba','Real Madrid','out','Ahilova tetiva'),('Gabriel Deck','Real Madrid','out','rame, posle operacije')]
st['injuries']={'round':'9','at':'29.10.2026. 7:00','src':'Eurodevotion, izveštaj o povredama za 29. oktobar','list':[{'p':a,'t':b,'s':c,'note':d} for a,b,c,d in INJ]}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(sys.argv[1],'w').write(h); print('ok',len(off['picks']))
