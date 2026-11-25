import json,collections,math,itertools,random
exec(open('/tmp/analiza24.py').read().split('# 1)')[0].replace('(131,132,133,134,135,136)','(137,138,139,140)'))
D=E+'/minusi/arhiva/kola/r14d2/'
A=json.load(open(f'{E}/baza/ponude/admiral/2026-11-25_b.json'))['picks']
st=collections.defaultdict(lambda:[0,0]); dnp=0; ev=0
for x in A:
    r=ishod(x['p'],x['s'],x['l'])
    if r is None: dnp+=1; continue
    st[x['s']][0]+=r; st[x['s']][1]+=1; st['sve'][0]+=r; st['sve'][1]+=1; ev+=(x['u'] if r else 0)-1
print('CELA PONUDA ispod:',{k:f"{a}/{n} ({a/n:.0%})" for k,(a,n) in st.items()},'ne igra',dnp,'ravnomerno %+.1f jed'%ev)
FT={'Real Madrid','Baskonia','Partizan'}
by=collections.defaultdict(lambda:[0,0]);
for x in A:
    r=ishod(x['p'],x['s'],x['l'])
    if r is None: continue
    k='filtrirani timovi' if x['t'] in FT else 'ostali'; by[k][0]+=r; by[k][1]+=1
print('  po filteru',{k:f"{a}/{n} ({a/n:.0%})" for k,(a,n) in by.items()})
# naš izbor
P=json.load(open(D+'sel_v5.json')); mix={(x['p'],x['s']):x['pr'] for x in P}
T=json.load(open(E+'/minusi/planovi/plan_admiral_65_25nov_odigrano.txt'))['tickets']
iu=collections.Counter((l['p'],l['s'],l['l']) for t in T for l in t['legs'])
ok=n=0;okm=nm=0; tier=collections.defaultdict(lambda:[0,0,0,0])
for (p,s,l),c in iu.items():
    r=ishod(p,s,l)
    if r is None: continue
    ok+=r;n+=1;okm+=r*c;nm+=c
    m=mix.get((p,s),.55); k='≥0,62' if m>=.62 else '0,58–0,62' if m>=.58 else '0,54–0,58' if m>=.54 else '<0,54'
    tier[k][0]+=r;tier[k][1]+=1;tier[k][2]+=r*c;tier[k][3]+=c
print('NAŠ IZBOR: stavke %d/%d (%.0f%%), po mestima %d/%d (%.0f%%)'%(ok,n,100*ok/n,okm,nm,100*okm/nm))
for k in ('≥0,62','0,58–0,62','0,54–0,58','<0,54'):
    a=tier[k]; print('   ',k,'stavke %d/%d'%(a[0],a[1]),'mesta %d/%d (%.0f%%)'%(a[2],a[3],100*a[2]/max(a[3],1)))
# raspodela promašaja
def misses(t):
    m=0;v=0
    for l in t['legs']:
        r=ishod(l['p'],l['s'],l['l'])
        if r is None: v+=1
        elif not r: m+=1
    return m,v
mc=collections.Counter(); bysize=collections.defaultdict(collections.Counter)
for t in T:
    m,v=misses(t); mc[m]+=1; bysize[len(t['legs'])][m]+=1
print('PROMAŠAJI po tiketu',dict(sorted(mc.items())),{k:dict(sorted(v.items())) for k,v in sorted(bysize.items())})
# najteži padovi
fall=sorted([(c,p,s,l,box(p)[s] if box(p) else None) for (p,s,l),c in iu.items() if ishod(p,s,l) is False],reverse=True)
print('NAJTEŽI PADOVI',[(f"{p.split()[-1]} {s}{l} ({v})",c) for c,p,s,l,v in fall[:12]])
print('max stavka',max(iu.values()),'od',len(T))
# shuffle test: isti parovi, nasumično raspoređeni u tikete istih veličina (bez istog igrača 2x)
legs=[l for t in T for l in t['legs']]; sizes=[len(t['legs']) for t in T]
res=[ishod(l['p'],l['s'],l['l']) for l in legs]
rnd=random.Random(5); clean=[];one=[]
for it in range(2000):
    idx=list(range(len(legs))); rnd.shuffle(idx); pos=0; c0=c1=0
    for s in sizes:
        tk=idx[pos:pos+s]; pos+=s
        m=sum(1 for i in tk if res[i] is False)
        c0+=m==0; c1+=m==1
    clean.append(c0); one.append(c1)
print('NASUMIČNO RASPOREĐENI ISTI PAROVI: čistih tiketa prosek %.2f (P>=1: %.0f%%), sa 1 promašajem %.1f | stvarno čistih %d, sa 1 %d'%(sum(clean)/len(clean),100*sum(1 for c in clean if c>=1)/len(clean),sum(one)/len(one),mc[0],mc[1]))
