import json,itertools,math,collections,random
st=json.load(open('minusi/aplikacija/stanje.json'))
R=st['results']
def bon(n):
    T={4:.03,5:.04,6:.07,7:.11,8:.16,9:.21,10:.26}
    return T.get(n, .26+.05*(n-10) if n>10 else 0)
def ls(t,l):
    r=R.get('|'.join([str(t['round']).strip(),l['p'].strip().lower(),l['stat'],str(l['line'])]))
    if not r: return None
    if r.get('dnp'): return 'v'
    a=r.get('actual')
    if a is None: return {'hit':'h','miss':'m','void':'v'}.get(r.get('outcome'))
    return 'h' if a<l['line'] else 'm' if a>l['line'] else 'v'
T=[]
for t in st['tickets']:
    s=[ls(t,l) for l in t['legs']]
    if None in s: continue
    T.append((t,s))
print('tiketa sa rezultatom',len(T),'od',len(st['tickets']))
# legs
legs=[(l,s) for t,ss in T for l,s in zip(t['legs'],ss) if s!='v']
h=sum(s=='h' for l,s in legs); print('parovi po mestima: %d/%d = %.1f%%, prosečna kvota %.2f, potrebno za nulu %.1f%%'%(h,len(legs),100*h/len(legs),sum(l['odds'] for l,s in legs)/len(legs),100/ (sum(l['odds'] for l,s in legs)/len(legs))))
# by size
by=collections.defaultdict(lambda:{'n':0,'stake':0,'ret':0,'won':0,'refund':0,'miss':collections.Counter(),'pp':0})
for t,ss in T:
    n=len(t['legs']); b=by[n]; b['n']+=1; b['stake']+=t['stake']
    nv=[ (l,s) for l,s in zip(t['legs'],ss) if s!='v']
    m=sum(s=='m' for l,s in nv); b['miss'][m]+=1
    if m==0:
        o=math.prod(l['odds'] for l,s in nv); pay=t['stake']*o*(1+bon(len(nv))) if t.get('bonus') is None else t['stake']*o+t['bonus']; b['ret']+=pay; b['won']+=1
    else: b['ret']+=t.get('refund',0) or 0; b['refund']+=t.get('refund',0) or 0
    # expected P(win) from leg rate
for n in sorted(by):
    b=by[n]; print(f"{n:2} parova: tiketa {b['n']:4} ulog {b['stake']:7.0f} vraćeno {b['ret']:8.0f} ({b['ret']/b['stake']-1:+.0%}) dobitnih {b['won']:3} povraćaj {b['refund']:6.0f} promašaji {dict(sorted(b['miss'].items()))}")
tot_s=sum(b['stake'] for b in by.values()); tot_r=sum(b['ret'] for b in by.values())
print('UKUPNO minusi ulog %.0f vraćeno %.0f (%+.1f%%)'%(tot_s,tot_r,100*(tot_r/tot_s-1)))
# per round
pr=collections.defaultdict(lambda:[0,0,0,0,0])
for t,ss in T:
    nv=[(l,s) for l,s in zip(t['legs'],ss) if s!='v']; m=sum(s=='m' for l,s in nv)
    x=pr[(t['round'],t['date'])]; x[0]+=1; x[1]+=t['stake']
    x[3]+=sum(s=='h' for l,s in nv); x[4]+=len(nv)
    if m==0: x[2]+=t['stake']*math.prod(l['odds'] for l,s in nv)*(1+bon(len(nv)))
    else: x[2]+=t.get('refund',0) or 0
print('po danu: kolo datum tiketa ulog vraćeno pogodnost_parova')
for k in sorted(pr,key=lambda k:k[1]): x=pr[k]; print(' ',k[0],k[1],x[0],x[1],round(x[2]),'%.0f%%'%(100*x[3]/x[4]))
# sub-tickets: same legs, random k-subsets
print('ISTI PAROVI, KRAĆI TIKETI (sve kombinacije k parova iz svakog odigranog tiketa, ulog 1):')
for k in (2,3,4,5,6,8):
    cnt=0; win=0; ret=0
    for t,ss in T:
        nv=[(l,s) for l,s in zip(t['legs'],ss) if s!='v']
        if len(nv)<k: continue
        combs=list(itertools.combinations(nv,k))
        if len(combs)>60: combs=random.Random(1).sample(combs,60)
        for c in combs:
            cnt+=1
            if all(s=='h' for l,s in c): win+=1; ret+=math.prod(l['odds'] for l,s in c)*(1+bon(k))
    print(f"  {k} parova: dobitnih {100*win/cnt:5.2f}% , povraćaj {ret/cnt-1:+.1%}  (uzoraka {cnt})")
print()
for a,b in (('2026-09-01','2026-11-04'),('2026-11-05','2026-11-30')):
    sel=[(t,ss) for t,ss in T if a<=t['date']<=b]
    L=[(l,s) for t,ss in sel for l,s in zip(t['legs'],ss) if s!='v']
    h=sum(s=='h' for l,s in L); ao=sum(l['odds'] for l,s in L)/len(L)
    e8=[(t,ss) for t,ss in sel if len(t['legs'])==8]
    p=h/len(L)
    mc=collections.Counter(sum(s=='m' for s in ss if s!='v') for t,ss in e8)
    n=len(e8)
    binom={k:round(n*math.comb(8,k)*(1-p)**k*p**(8-k),1) for k in range(0,5)}
    print(f"{a}..{b}: parovi {h}/{len(L)} = {100*p:.1f}% kvota {ao:.2f} | osmica {n}, dobitnih {mc[0]}, očekivano {n*p**8:.1f} | promašaji stvarno {dict(sorted(mc.items()))} | binomno {binom}")
    st_=sum(t['stake'] for t,ss in sel); print('   ulog',st_)
O=st['opsezi']; s=sum(o['stake'] for o in O); 
def oi(o):
    stt='w'
    for l in o['legs']:
        if l.get('dnp'): continue
        if l.get('actual') is None: return 'p'
        if not (l['lo']<=l['actual']<=l['hi']): stt='l'
    return stt
w=[o for o in O if oi(o)=='w']; print('opsezi tiketa',len(O),'ulog',s,'dobitnih',len(w),'isplata',sum(o.get('payout',0) for o in w))
