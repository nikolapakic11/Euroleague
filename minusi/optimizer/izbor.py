"""Pretvara kandidate iz Generatora (izlaz scrape.py) u ulaz za optimizer (optg7.py).
Upotreba: python3 izbor.py <pool.json> <ponuda.json> <sel.json> [--najmanja 1.65] [--sa-zatamnjenim]
 - spaja kandidate sa ponudom (šifra, kvota ispod, vreme), računa tržišnu verovatnoću 'fair' i kod utakmice 'g' (DOMAĆIN-GOST)
 - podrazumevano izostavlja redove koje aplikacija zatamni (izbačeni ili ispod najmanje kvote) i kvote ispod --najmanja"""
import json,sys,os,argparse,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import BAZA
ap=argparse.ArgumentParser(); ap.add_argument('pool'); ap.add_argument('ponuda'); ap.add_argument('izlaz')
ap.add_argument('--najmanja',type=float,default=1.65); ap.add_argument('--sa-zatamnjenim',action='store_true'); a=ap.parse_args()
NAME2CODE={'Dubai':'DUB','Hapoel Tel-Aviv':'HTA','Hapoel Tel Aviv':'HTA','Anadolu Efes':'IST','Panathinaikos':'PAN','Zalgiris Kaunas':'ZAL','Partizan':'PAR','Lyon-Villeurbanne':'ASV','Asvel':'ASV','Baskonia':'BAS','Olympiacos':'OLY','Olimpia Milano':'MIL','Armani Milano':'MIL','Barcelona':'BAR','Valencia':'PAM','Virtus Bologna':'VIR','Besiktas':'BES','Bayern':'MUN','Bayern Munich':'MUN','Crvena Zvezda':'RED','Maccabi Tel Aviv':'TEL','Paris':'PRS','Real Madrid':'MAD','Fenerbahce':'ULK'}
STAT={'Poeni':'P','Skokovi':'S','Asistencije':'A'}
off=json.load(open(a.ponuda,encoding='utf8'))['picks']; pool=json.load(open(a.pool,encoding='utf8'))['pool']
G=json.load(open(BAZA+'/games.json'))['data']
def dan(t): m=re.search(r'(\d\d)\. (\d\d)\. (\d{4})',t); return f'{m.group(3)}-{m.group(2)}-{m.group(1)}'
def igra(day,t1):
    for g in G:
        if g['date'][:10]==day:
            h,r=g['local']['club']['code'],g['road']['club']['code']
            if t1 in (h,r): return h+'-'+r
    return None
idx={(o['p'],o['s'],o['l']):o for o in off}
sel=[];skip={'zatamnjen':0,'niska kvota':0,'bez ponude':0,'bez utakmice':0}
for x in pool:
    if x['dim'] and not a.sa_zatamnjenim: skip['zatamnjen']+=1; continue
    if x['u']<a.najmanja-1e-9: skip['niska kvota']+=1; continue
    s=STAT[x['s']]; o=idx.get((x['p'],s,x['l']))
    if not o: skip['bez ponude']+=1; continue
    g=igra(dan(o['time']),NAME2CODE[o['t']])
    if not g: skip['bez utakmice']+=1; continue
    fair=(1/o['u'])/((1/o['u'])+(1/o['o']))
    sel.append({'c':o['c'],'p':x['p'],'t':o['t'],'s':s,'l':x['l'],'u':o['u'],'o':o['o'],'pr':x['pr'],'fair':round(fair,4),'g':g,'time':o['time'],'cls':s,'role':x['role'],'star':x['star']})
json.dump(sel,open(a.izlaz,'w',encoding='utf8'),ensure_ascii=False)
print('izabrano',len(sel),'od',len(pool),'| izostavljeno',skip,'| utakmica',sorted({x['g'] for x in sel}))
