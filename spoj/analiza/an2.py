import json,math,collections
exec(open('spoj/analiza/an.py').read().split("print('== A.")[0])
def rang_dan(R,key,out):
    byd=collections.defaultdict(list)
    for x in R: byd[x['dan']].append(x)
    for L in byd.values():
        L.sort(key=lambda x:-x[key])
        for i,x in enumerate(L): x[out]=i/len(L)
rang_dan(A,'pu','r_pu'); rang_dan(A,'msig','r_ms')
for x in A: x['pfix']=sg(x['Lq']+0.15*(lg(x['mpu'])-x['Lq']-0.16)+0.30*x['pu']); x['ev']=x['pfix']*x['u']
rang_dan(A,'ev','r_ev')
P1=[x for x in A if x['kolo']<=7]; P2=[x for x in A if x['kolo']>=8]
def two(nm,f): print(f"  {nm:44s} | kola 4-7: "+line('',[x for x in P1 if f(x)])[2:]+"\n  {:44s} | kola 8-11: ".format('')+line('',[x for x in P2 if f(x)])[2:])
print('== Stabilnost po periodima (Admiral)')
two('sve',lambda x:True)
two('skokovi i asistencije',lambda x:x['s']!='P'); two('poeni',lambda x:x['s']=='P'); two('poeni 7,5-10,5',lambda x:x['s']=='P' and 6.5<x['l']<=10.5); two('poeni 11,5-14,5',lambda x:x['s']=='P' and 10.5<x['l']<=14.5); two('asistencije 3,5+',lambda x:x['s']=='A' and x['l']>2.5)
two('izostanci < 15 min',lambda x:x['missmin']<15); two('izostanci 15-35',lambda x:15<=x['missmin']<35); two('izostanci 35+',lambda x:x['missmin']>=35)
two('granica ispod proseka igrača (zline<-0,17)',lambda x:x['zline']<-0.17); two('granica iznad proseka (zline>0,13)',lambda x:x['zline']>0.13)
two('oba modela se slažu (najjačih 30%)',lambda x:x['r_pu']<.3 and x['r_ms']<.3); two('oba se slažu i izostanci < 35',lambda x:x['r_pu']<.3 and x['r_ms']<.3 and x['missmin']<35)
two('oba se slažu, S ili A',lambda x:x['r_pu']<.3 and x['r_ms']<.3 and x['s']!='P'); two('oba se slažu, poeni',lambda x:x['r_pu']<.3 and x['r_ms']<.3 and x['s']=='P')
two('spoj: najboljih 25% dana po vrednosti',lambda x:x['r_ev']<.25); two('spoj: sredina 25-60%',lambda x:.25<=x['r_ev']<.6); two('spoj: donjih 40%',lambda x:x['r_ev']>=.6)
two('donjih 40% bez izostanaka 35+ i bez P 7,5-10,5',lambda x:x['r_ev']>=.6 and x['missmin']<35 and not (x['s']=='P' and 6.5<x['l']<=10.5))
two('najboljih 60% bez izostanaka 35+',lambda x:x['r_ev']<.6 and x['missmin']<35)
print('\n== Sajt (predlozi)')
for k in (10,11):
    d=json.load(open(f'/home/claude/Euroleague/procene/predlozi/kolo{k}.json'))['predlozi']
    for side,nm in (('u','MINUS'),('o','PLUS')):
        P=[p for p in d if p['strana']==side and p.get('ishod') is not None]
        hit=[(p['ishod']<p['l']) if side=='u' else (p['ishod']>p['l']) for p in P]
        if P: print(f"  kolo {k} {nm}: {sum(hit)}/{len(P)}, prosečna kvota {sum(p['kvota'] for p in P)/len(P):.2f}, povraćaj {sum((p['kvota']-1) if h else -1 for p,h in zip(P,hit))/len(P):+.0%}")
