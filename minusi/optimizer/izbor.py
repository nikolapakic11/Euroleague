"""Pretvara kandidate iz Generatora (izlaz scrape.py) u ulaz za optimizer (optg7.py).
Upotreba: python3 izbor.py <pool.json> <ponuda.json> <sel.json> [--najmanja 1.65] [--sa-zatamnjenim] [--bez-procena]
 - spaja kandidate sa ponudom (šifra, kvota ispod, vreme), računa tržišnu verovatnoću 'fair' i kod utakmice 'g' (DOMAĆIN-GOST)
 - podrazumevano izostavlja redove koje aplikacija zatamni (izbačeni ili ispod najmanje kvote) i kvote ispod --najmanja
 - od 7.11.2026 u verovatnoću 'pr' ulazi i model procena (spoj/signali.py: tržište + 0,15·minus + 0,30·procene);
   provera u spoj/provera/izvestaj.md. Sa --bez-procena ostaje stara verovatnoća (tržište + 0,15·minus).
 - od 12.11.2026 'pr' je naučeni spoj (signali.spoj2: tržište + oba modela + izostanci u timu + granica prema proseku +
   kazna za poene 7,5-10,5; težine spoj/tezine.json). Stari spoj ostaje u 'pr1'. Pravila (spoj/analiza/IZVESTAJ_2026-11-12.md):
     filter 'izostanci': timu fali 35+ minuta rotacije (--povrede, podrazumevano procene/podaci/povrede.json; --van k1,k2
       ručno odsutni, --igra k1,k2 ručno prisutni), osim poena igrača koji je 3-5. strelac tima;
     filter 'granica podignuta': prema ranijem snimku iste kladionice (--ranija ponuda.json);
     nivo 'A': oba modela u najjačih 30% dana i bez filtera (66-68% u proveri); --vrh 0.30 ostavlja nivo A i najboljih 30% po vrednosti;
     --bez-filtera ostavlja sve."""
import json,sys,os,argparse,re
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
from putanje import BAZA
ap=argparse.ArgumentParser(); ap.add_argument('pool'); ap.add_argument('ponuda'); ap.add_argument('izlaz')
ap.add_argument('--najmanja',type=float,default=1.60); ap.add_argument('--sa-zatamnjenim',action='store_true'); ap.add_argument('--bez-procena',action='store_true')
ap.add_argument('--povrede'); ap.add_argument('--van',default=''); ap.add_argument('--igra',default=''); ap.add_argument('--ranija'); ap.add_argument('--vrh',type=float); ap.add_argument('--bez-filtera',action='store_true'); a=ap.parse_args()
sys.path.insert(0,os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','..','spoj'))
import signali
SIG=None if a.bez_procena else signali.Signali()
bez_pm=0
NAME2CODE={'Dubai':'DUB','Hapoel Tel-Aviv':'HTA','Hapoel Tel Aviv':'HTA','Anadolu Efes':'IST','Panathinaikos':'PAN','Zalgiris Kaunas':'ZAL','Partizan':'PAR','Lyon-Villeurbanne':'ASV','Asvel':'ASV','Baskonia':'BAS','Olympiacos':'OLY','Olimpia Milano':'MIL','Armani Milano':'MIL','Barcelona':'BAR','Valencia':'PAM','Virtus Bologna':'VIR','Besiktas':'BES','Bayern':'MUN','Bayern Munich':'MUN','Crvena Zvezda':'RED','Crvena zvezda':'RED','Maccabi Tel Aviv':'TEL','Paris':'PRS','Real Madrid':'MAD','Fenerbahce':'ULK'}
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
POV={}
if SIG:
    pp=a.povrede or os.path.join(signali.KOREN,'procene','podaci','povrede.json')
    try: POV={k:dict(v) for k,v in json.load(open(pp,encoding='utf8'))['igraci'].items()}
    except Exception as e: print('povrede nisu učitane:',e)
    for k in filter(None,(z.strip().lower() for z in a.van.split(','))): POV[k]={'stanje':'van','tekst':'ručno'}
    for k in filter(None,(z.strip().lower() for z in a.igra.split(','))): POV[k]={'stanje':'igra','tekst':'ručno'}
RAN={}
if a.ranija:
    for o in json.load(open(a.ranija,encoding='utf8'))['picks']:
        if o.get('s') in ('P','S','A') and o.get('u') and o.get('o'): RAN[(o['p'],o['s'])]=o
IZ={}
sel=[];skip={'zatamnjen':0,'niska kvota':0,'bez ponude':0,'bez utakmice':0}
for x in pool:
    if x['dim'] and not a.sa_zatamnjenim: skip['zatamnjen']+=1; continue
    if x['u']<a.najmanja-1e-9: skip['niska kvota']+=1; continue
    s=STAT[x['s']]; o=idx.get((x['p'],s,x['l']))
    if not o: skip['bez ponude']+=1; continue
    g=igra(dan(o['time']),NAME2CODE[o['t']])
    if not g: skip['bez utakmice']+=1; continue
    fair=(1/o['u'])/((1/o['u'])+(1/o['o']))
    lg=lambda q:__import__('math').log(min(max(q,1e-3),1-1e-3)/(1-min(max(q,1e-3),1-1e-3)))
    pa=x['pr']  # procena modela aplikacije (stara, precenjuje nivo ~5 poena)
    prc=1/(1+__import__('math').exp(-(lg(fair)+0.15*(lg(pa)-lg(fair)-0.16))))  # backtest: tržište + mala korekcija modela
    pm=None
    if SIG:
        tc=NAME2CODE[o['t']]; h,r=g.split('-'); k,_=SIG.nadji(x['p'],o['t'],tc)
        if k: pm=SIG.procene_preko(k,dan(o['time']),tc,r if tc==h else h,s,x['l'])
        if pm is None: bez_pm+=1
    pr1=signali.spoj_ispod(fair,pa,pm) if pm is not None else prc
    pr=pr1; msig=miss=zl=rg=None; filt=None; van_tim=[]
    if SIG and k:
        d0=dan(o['time']); opp=r if tc==h else h
        m=SIG.minus(k,d0,tc,opp,s,x['l'],fair); msig=m['msig'] if m else None
        if tc not in IZ: IZ[tc]=signali.izostanci(SIG,tc,d0,POV)
        miss=round(sum(v for kk,v in IZ[tc].items() if kk!=k),1); van_tim=sorted(IZ[tc],key=lambda kk:-IZ[tc][kk])
        zl=signali.zline(SIG,k,d0,s,x['l']); rg=signali.rang_u_timu(SIG,k,tc,d0,s)
        ro=RAN.get((x['p'],s)); spu=bool(ro and x['l']<ro['l'])     # granica spuštena od ranijeg snimka: ispod prolazi češće
        pr=signali.spoj2(fair,pm,msig,miss,zl,s,x['l'],signali.dodatne(SIG,k,tc,opp,d0,s),spu)
        if miss>=signali.IZOSTANCI_PRAG and not (s=='P' and rg and 3<=rg<=5): filt='izostanci'
        ro=RAN.get((x['p'],s))
        if ro:
            f0=(1/ro['o'])/((1/ro['u'])+(1/ro['o']))
            if x['l']>ro['l'] or (x['l']==ro['l'] and (1-fair)-f0>=0.03): filt='granica podignuta'
    sel.append({'c':o['c'],'p':x['p'],'t':o['t'],'s':s,'l':x['l'],'u':o['u'],'o':o['o'],'pr':round(pr,4),'pr1':round(pr1,4),'pr_staro':round(prc,4),'pm':round(pm,4) if pm is not None else None,'pr_app':pa,'fair':round(fair,4),
                'msig':msig,'pu':round(lg(1-pm)-lg(fair),3) if pm is not None else None,'miss':miss,'zl':round(zl,2) if zl is not None else None,'rang':rg,'spustena':(spu if SIG and k else False),'filt':filt,'g':g,'time':o['time'],'cls':s,'role':x['role'],'star':x['star']})
# nivo A: oba modela u najjačih 30% dana (rang unutar dana), bez filtera
import collections
byd=collections.defaultdict(list)
for x in sel: byd[dan(x['time'])].append(x)
for L in byd.values():
    for key in ('pu','msig'):
        R=sorted([x for x in L if x[key] is not None],key=lambda x:-x[key])
        for i,x in enumerate(R): x['r_'+key]=round(i/len(R),3)
    R=sorted(L,key=lambda x:-x['pr']*x['u'])
    for i,x in enumerate(R): x['r_v']=round(i/len(R),3)
for x in sel: x['nivo']='A' if (x.get('r_pu',1)<.3 and x.get('r_msig',1)<.3 and not x['filt']) else 'B'
svi=len(sel); nf=collections.Counter(x['filt'] for x in sel if x['filt'])
if not a.bez_filtera: sel=[x for x in sel if not x['filt']]
if a.vrh: sel=[x for x in sel if x['nivo']=='A' or x['r_v']<a.vrh]
sel.sort(key=lambda x:-x['pr']*x['u'])
json.dump(sel,open(a.izlaz,'w',encoding='utf8'),ensure_ascii=False)
print('filteri:',dict(nf),'| posle filtera i vrha:',len(sel),'od',svi,'| nivo A:',sum(x['nivo']=='A' for x in sel))
print('izostanci po timu (min):',{t:(round(sum(v.values())),list(v)) for t,v in IZ.items()})
print('izabrano',len(sel),'od',len(pool),'| izostavljeno',skip,'| utakmica',sorted({x['g'] for x in sel}),'| bez procene modela (stara verovatnoća)',bez_pm if SIG else 'sve (--bez-procena)')
