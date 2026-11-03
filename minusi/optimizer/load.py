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
A=[("Dubai","Hapoel Tel Aviv",1.65,2.25,175.5,88.5,86.5),("Anadolu Efes","Panathinaikos",3.1,1.37,164.5,79.5,85.5),("Zalgiris Kaunas","Partizan",1.3,3.55,165.5,86.5,79.5),("Asvel","Baskonia",1.55,2.47,175.5,89.5,86.5),("Olympiacos","Armani Milano",1.17,5,167.5,88.5,78.5),("Barcelona","Valencia",1.68,2.2,183.5,92.5,90.5),("Virtus Bologna","Besiktas",1.43,2.85,175.5,90.5,85.5)]
st['lines']={'at':'2026-10-30T09:12:39.818Z','src':'AdmiralBet, kvote utakmica 30.10. u 10:12','games':{CODE[a]+'-'+CODE[b]:{'total':t,'hTot':ht,'aTot':at,'ml1':m1,'ml2':m2} for a,b,m1,m2,t,ht,at in A}}
INJ=[('Justin Anderson','Dubai','out','zadnja loža'),('Thomas Walkup','Dubai','out','leđa'),('Klemen Prepelic','Dubai','dtd','leđa'),('Mam Jaiteh','Dubai','out','Ahilova tetiva'),
 ('Alec Peters','Olimpia Milano','dtd','kontuzija levog kolena'),
 ('Devon Dotson','Besiktas','dtd','izostavljen iz sastava'),('Lonnie Walker','Besiktas','dtd','noga'),('DaQuan Jeffries','Besiktas','out','zglob šake'),
 ('Umoja Gibson','Barcelona','doubtful','udarac u koleno'),('Yoan Makoundou','Barcelona','out','koleno'),('Juan Nunez','Barcelona','out','uganuće skočnog zgloba, oko 10 dana'),
 ('Tyler Ennis','Hapoel Tel-Aviv','out','Ahilova tetiva'),('Tamir Blatt','Hapoel Tel-Aviv','dtd','van sastava'),
 ('Nikos Rogkavopoulos','Panathinaikos','dtd','zadnja loža'),('Mathis Dossou-Yovo','Lyon-Villeurbanne','out','prepona'),('Juhann Begarin','Lyon-Villeurbanne','doubtful','povreda'),
 ('Chris Duarte','Baskonia','dtd','mišić'),('Rodions Kurucs','Baskonia','dtd','povreda'),('Tadas Sedekerskis','Baskonia','out','mišić butine'),
 ('Tyler Dorsey','Olympiacos','out','suspenzija kluba, mesec dana'),('Evan Fournier','Olympiacos','out','rame i koleno'),('Jean Montero','Olympiacos','out','skočni zglob i koleno'),('Nikola Milutinov','Olympiacos','dtd','nožni prst'),
 ('Mike James','Anadolu Efes','out','Ahilova tetiva'),('Isaia Cordinier','Anadolu Efes','out','oporavak'),('Georgios Papagiannis','Anadolu Efes','out','koleno'),('PJ Dozier','Anadolu Efes','out','leđa'),
 ('Nigel Williams-Goss','Zalgiris Kaunas','out','zadnja loža'),('Vanja Marinkovic','Partizan','out','Ahilova tetiva'),('Tonye Jekiri','Partizan','out','prepona')]
st['injuries']={'round':'9','at':'30.10.2026. 10:15','src':'Basketnews (lista povređenih za 9. kolo), raniji izveštaji za Efes, Žalgiris i Partizan','list':[{'p':a,'t':b,'s':c,'note':d} for a,b,c,d in INJ]}
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(sys.argv[1],'w').write(h); print('ok',len(off['picks']))
