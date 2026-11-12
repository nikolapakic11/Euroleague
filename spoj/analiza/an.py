import json,math,collections,statistics as st
import numpy as np
F=json.load(open('spoj/analiza/F.json')); MV=json.load(open('spoj/analiza/MV.json'))
lg=lambda p: math.log(min(max(p,.02),.98)/(1-min(max(p,.02),.98))); sg=lambda z:1/(1+math.exp(-z))
for x in F: x['q']=1-x['tr']; x['Lq']=lg(x['q']); x['pu']=-(lg(x['pm'])-lg(x['tr'])); x['absdiff']=abs(x['mdiff']); x['fav']=x['mdiff']
A=[x for x in F if x['izvor']=='admiral']
def roi(R): return sum((r['u']-1) if r['y'] else -1 for r in R)/len(R) if R else 0
def line(nm,R):
    if not R: return f"{nm}: -"
    n=len(R); y=sum(r['y'] for r in R)/n; q=sum(r['q'] for r in R)/n; z=(sum(r['y']-r['q'] for r in R))/math.sqrt(sum(r['q']*(1-r['q']) for r in R))
    return f"{nm}: n={n} ispod {y:.1%} (tržište {q:.1%}, razlika {y-q:+.1%}, z={z:+.1f}) povraćaj {roi(R):+.1%}"
print('== A. Admiral: osnovna pristrasnost tržišta (uvek ispod)')
for k in sorted({x['kolo'] for x in A}): print('  '+line(f'kolo {k}',[x for x in A if x['kolo']==k]))
for s in 'PSA': print('  '+line('stavka '+s,[x for x in A if x['s']==s]))
for nm,f in (('P do 6,5',lambda x:x['s']=='P' and x['l']<=6.5),('P 7,5-10,5',lambda x:x['s']=='P' and 6.5<x['l']<=10.5),('P 11,5-14,5',lambda x:x['s']=='P' and 10.5<x['l']<=14.5),('P 15,5+',lambda x:x['s']=='P' and x['l']>14.5),
              ('S do 3,5',lambda x:x['s']=='S' and x['l']<=3.5),('S 4,5+',lambda x:x['s']=='S' and x['l']>3.5),('A do 2,5',lambda x:x['s']=='A' and x['l']<=2.5),('A 3,5+',lambda x:x['s']=='A' and x['l']>2.5),
              ('kvota ispod < 1,70',lambda x:x['u']<1.7),('1,70-1,84',lambda x:1.7<=x['u']<1.85),('1,85-1,99',lambda x:1.85<=x['u']<2),('2,00+',lambda x:x['u']>=2),
              ('min. < 15',lambda x:x['am']<15),('15-20',lambda x:15<=x['am']<20),('20-25',lambda x:20<=x['am']<25),('25+',lambda x:x['am']>=25),('domaćin',lambda x:x['dom']==1),('gost',lambda x:x['dom']==0)):
    print('  '+line(nm,[x for x in A if f(x)]))
print('\n== B. Kandidati za nove parametre (Admiral, sva kola): trećine, razlika od tržišta')
feats=['pu','msig','zline','hot','mintrend','emp','st','mdiff','absdiff','rest','missmin','retmin','rang','mcv','n','am']
for f in feats:
    R=sorted([x for x in A if x.get(f) is not None],key=lambda x:x[f]); n=len(R)
    parts=[R[:n//3],R[n//3:2*n//3],R[2*n//3:]]
    print(f"  {f:9s} "+' | '.join(f"[{p[0][f]:.2f}..{p[-1][f]:.2f}] {sum(r['y'] for r in p)/len(p):.1%} ({sum(r['y']-r['q'] for r in p)/len(p):+.1%}, povr. {roi(p):+.0%})" for p in parts))
def fit(R,fs,l2=2.0):
    X=np.array([[1]+[r[f] for f in fs] for r in R],float); y=np.array([r['y'] for r in R],float); off=np.array([r['Lq'] for r in R]); w=np.zeros(X.shape[1])
    for _ in range(60):
        p=1/(1+np.exp(-(off+X@w))); g=X.T@(p-y)+l2*np.r_[0,w[1:]]; H=(X.T*(p*(1-p)))@X+l2*np.diag(np.r_[0,np.ones(len(w)-1)]); w-=np.linalg.solve(H,g)
    return w
def wf(R,fs,kola=(7,8,9,10,11),key=None):
    L=0;n=0;w=None
    for k in kola:
        tr=[r for r in R if r['kolo']<k]; te=[r for r in R if r['kolo']==k]
        if not te: continue
        w=fit(tr,fs)
        for r in te:
            p=sg(r['Lq']+w[0]+sum(wi*r[f] for wi,f in zip(w[1:],fs))); p=min(max(p,1e-4),1-1e-4)
            if key: r[key]=p
            L+=-(math.log(p) if r['y'] else math.log(1-p)); n+=1
    return L/n,w
# standardizacija
for f in feats+['dom']:
    v=[x[f] for x in A if x.get(f) is not None]; m=st.mean(v); s=st.pstdev(v) or 1
    for x in F: x['z_'+f]=((x[f]-m)/s) if x.get(f) is not None else 0.0
print('\n== C. Walk-forward (Admiral, test kola 7-11): log gubitak ×1000 (manje je bolje)')
b0,_=wf(A,[]); b1,w1=wf(A,['z_pu','z_msig']); print(f"  samo tržište {b0*1000:.1f} | + oba modela {b1*1000:.1f} (dobitak {1000*(b0-b1):+.1f}) težine {np.round(w1,2)}")
res=[]
for f in ['zline','hot','mintrend','emp','st','mdiff','absdiff','rest','missmin','retmin','rang','mcv','n','am','dom']:
    L,w=wf(A,['z_pu','z_msig','z_'+f]); res.append((1000*(b1-L),f,round(float(w[-1]),3)))
for d,f,w in sorted(res,reverse=True): print(f"  + {f:9s} dobitak {d:+.2f}  (težina {w:+.3f}; + znači više ispod)")
best=[f for d,f,w in sorted(res,reverse=True) if d>0.3][:5]; print('  najbolji zajedno:',best)
Lb,wb=wf(A,['z_pu','z_msig']+['z_'+f for f in best],key='pnew'); wf(A,['z_pu','z_msig'],key='pcur'); print(f"  svi zajedno: {Lb*1000:.1f} (dobitak prema oba modela {1000*(b1-Lb):+.1f}) težine {np.round(wb,2)}")
T=[x for x in A if x['kolo']>=7 and 'pnew' in x and x['u']>=1.6]
byd=collections.defaultdict(list)
for x in T: byd[x['dan']].append(x)
def top(key,frac):
    S=[]
    for L in byd.values(): L=sorted(L,key=lambda x:-x[key]*x['u']); S+=L[:max(1,int(len(L)*frac))]
    return S
for x in T: x['pfix']=sg(x['Lq']+0.15*(lg(x['mpu'])-x['Lq']-0.16)+0.30*x['pu'])
print('  izbor po vrednosti, najboljih 25% dana (kvota ≥1,60, kola 7-11):')
for nm,key in (('sadašnji spoj (fiksne težine)','pfix'),('naučeno: tržište+oba modela','pcur'),('naučeno + novi parametri','pnew')):
    for fr in (.25,.10): print('    '+line(f'{nm} {fr:.0%}',top(key,fr)))
print('\n== D. Odsutni saigrači (stvarni sastav; Admiral): da li korist ide prvoj opciji')
for nm,f in (('bez većih izostanaka (<15 min)',lambda x:x['missmin']<15),('izostanci 15-35 min',lambda x:15<=x['missmin']<35),('izostanci 35+ min',lambda x:x['missmin']>=35)):
    R=[x for x in A if f(x)]; print('  '+line(nm,R))
    for nm2,f2 in (('   poeni, rang 1-2 u timu',lambda x:x['s']=='P' and x['rang']<=2),('   poeni, rang 3-5',lambda x:x['s']=='P' and 3<=x['rang']<=5),('   poeni, rang 6+',lambda x:x['s']=='P' and x['rang']>=6),('   skokovi i asistencije',lambda x:x['s']!='P')):
        print('  '+line(nm2,[x for x in R if f2(x)]))
print('  povratnici (saigrač se vraća, 15+ min): '+line('',[x for x in A if x['retmin']>=15]))
print('\n== E. Razlika granica među kladionicama (kola 7, 10, 11; sve kladionice)')
M=[x for x in F if x['ldev'] is not None]
print('  '+line('granica VIŠA od medijane ostalih',[x for x in M if x['ldev']>0])); print('  '+line('granica ista',[x for x in M if x['ldev']==0])); print('  '+line('granica NIŽA od medijane',[x for x in M if x['ldev']<0]))
lo=[x for x in M if x['ldev']<0]; print(f"   -> PREKO na nižoj granici: {1-sum(x['y'] for x in lo)/len(lo):.1%}, povraćaj {sum((x['o']-1) if not x['y'] else -1 for x in lo)/len(lo):+.1%} (n={len(lo)})")
print('\n== F. Kretanje granice u toku dana (prva -> poslednja ponuda iste kladionice)')
def mvline(nm,R,side='u',when=1):
    if not R: print(f'  {nm}: -'); return
    l='l%d'%when; kv=('u%d' if side=='u' else 'o%d')%when
    hit=[(r['act']<r[l]) if side=='u' else (r['act']>r[l]) for r in R]
    print(f"  {nm}: n={len(R)} prošlo {sum(hit)/len(R):.1%}, povraćaj {sum((r[kv]-1) if h else -1 for r,h in zip(R,hit))/len(R):+.1%}")
up=[r for r in MV if r['l1']>r['l0'] or (r['l1']==r['l0'] and r['f1']-r['f0']>=0.03)]; dn=[r for r in MV if r['l1']<r['l0'] or (r['l1']==r['l0'] and r['f1']-r['f0']<=-0.03)]; same=[r for r in MV if r not in up and r not in dn]
print(f'  pomereno naviše {len(up)}, naniže {len(dn)}, bez promene {len(same)}')
mvline('naviše: ISPOD po RANOJ granici (rano igranje minusa)',up,'u',0); mvline('naviše: ISPOD po KASNOJ granici',up,'u',1); mvline('naviše: PREKO po RANOJ granici',up,'o',0)
mvline('naniže: ISPOD po RANOJ granici',dn,'u',0); mvline('naniže: ISPOD po KASNOJ granici',dn,'u',1); mvline('naniže: PREKO po KASNOJ granici',dn,'o',1)
mvline('bez promene: ISPOD',same,'u',1)
print('\n== G. Traženje PLUS-a (Admiral, sva kola): PREKO po podskupovima')
def ov(nm,R):
    if R: print(f"  {nm}: n={len(R)} preko {1-sum(r['y'] for r in R)/len(R):.1%}, povraćaj {sum((r['o']-1) if not r['y'] else -1 for r in R)/len(R):+.1%}")
ov('sve',A); ov('oba modela za preko (pu<-0.3 i msig<0)',[x for x in A if x['pu']<-0.3 and x['msig']<0]); ov('minuti u porastu (+4) i granica ispod proseka',[x for x in A if x['mintrend']>=4 and x['zline']<0])
ov('izostanci 35+ i rang 1-2 poeni',[x for x in A if x['missmin']>=35 and x['rang']<=2 and x['s']=='P']); ov('ranije retko ispod (emp<0.35)',[x for x in A if x['emp']<0.35]); ov('emp<0.35 i msig<0',[x for x in A if x['emp']<0.35 and x['msig']<0])
ov('kvota preko ≥ 2,00',[x for x in A if x['o']>=2.0]); ov('starter 25+ min, favorit (mdiff>5), domaćin',[x for x in A if x['am']>=25 and x['mdiff']>5 and x['dom']==1])
ov('hladan (hot<-0.7) i granica spuštena (zline<-0.3)',[x for x in A if x['hot']<-0.7 and x['zline']<-0.3])
