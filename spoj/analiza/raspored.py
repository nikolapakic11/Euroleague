import json,math,re,unicodedata,collections,random,statistics as st
import os; R0=os.path.abspath(os.path.join(os.path.dirname(__file__),'..','..'))
s=json.load(open(R0+'/minusi/aplikacija/stanje.json')); RES=s['results']
F=json.load(open(R0+'/spoj/analiza/F.json'))
lg=lambda p: math.log(min(max(p,.02),.98)/(1-min(max(p,.02),.98))); sg=lambda z:1/(1+math.exp(-z))
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r"[.']",'',t); t=re.sub(r'-',' ',t); t=re.sub(r'[^a-z ]','',t); return ' '.join(w for w in t.split() if w not in SUF)
PR={}
for x in F:
    if x['izvor']=='admiral':
        PR[(x['dan'],nk(x['k']),x['s'],x['l'])]=sg(lg(1-x['tr'])+0.15*(lg(x['mpu'])-lg(1-x['tr'])-0.16)+0.30*(lg(1-x['pm'])-lg(1-x['tr'])))
BON={4:.03,5:.05,6:.07,7:.11,8:.16,9:.21,10:.26,11:.26,12:.26}
def res(rd,l):
    r=RES.get(f"{rd}|{l['p'].lower()}|{l['stat']}|{l['line']}")
    if not r: return None
    return 'v' if r.get('dnp') else ('h' if r['actual']<l['line'] else 'm')
days=collections.defaultdict(list)
for t in s['tickets']: days[(t['round'],t['date'])].append(t)
def evaluate(tks,leg):
    w=pay=ref=0
    for st_,L in tks:
        rs=[leg[i]['r'] for i in L]; h=rs.count('h'); m=rs.count('m')
        if m==0 and h>0: w+=1; pay+=st_*math.prod(leg[i]['u'] for i in L if leg[i]['r']=='h')*(1+BON.get(h,0))
        if m==1 and h+m>=7: ref+=1; pay+=min(max(st_,100),500)
    return w,pay,ref
def build(sizes,stakes,cnt,leg,mode,R):
    left=collections.Counter(cnt); order=list(range(len(sizes)))
    order.sort(key=lambda k:sizes[k])
    tk={}
    def fill(k,key):
        t=[]
        for i in sorted([i for i in left if left[i]>0],key=key):
            if leg[i]['p'] not in {leg[j]['p'] for j in t}: t.append(i)
            if len(t)==sizes[k]: break
        for i in t: left[i]-=1
        tk[k]=t
    ntop={'slojevi':len(order),'hibrid':len(order)//3,'rasprseno':0}[mode]
    for n,k in enumerate(order):
        if n<ntop: fill(k,lambda i:(-leg[i]['p_'],R.random()))
        else: fill(k,lambda i:(-left[i]+R.random()*0.5,))   # raspršeno: najviše preostalih prvo, nasumično
    global NEPOT
    NEPOT[mode]+=sum(1 for k in range(len(sizes)) if len(tk[k])<sizes[k]); NUK[mode]+=len(sizes)
    return [(stakes[k],tk[k]) for k in range(len(sizes)) if len(tk[k])>=max(1,sizes[k]-1)]
NEPOT=collections.Counter(); NUK=collections.Counter()
tot=collections.defaultdict(lambda: collections.Counter()); perday=[]
for (rd,dt),T in sorted(days.items(),key=lambda x:x[0][1]):
    legs={}; tks=[]; ok=True
    for t in T:
        L=[]
        for l in t['legs']:
            r=res(rd,l); key=(l['p'],l['stat'],l['line'])
            if r is None: ok=False; break
            p=PR.get((dt,nk(l['p']),l['stat'],l['line']))
            if key not in legs: legs[key]=dict(p=l['p'],u=l['odds'],r=r,p_=p if p is not None else 1/l['odds']/1.04)
            L.append(key)
        if not ok: break
        tks.append((t['stake'],L))
    if not ok or int(rd)<4: continue
    keys=list(legs); ix={k:i for i,k in enumerate(keys)}; leg=[legs[k] for k in keys]
    actual=[(st_,[ix[k] for k in L]) for st_,L in tks]; sizes=[len(L) for _,L in actual]; stakes=[st_ for st_,_ in actual]
    cnt=collections.Counter(i for _,L in actual for i in L); ulog=sum(stakes)
    row={'dan':dt,'kolo':rd,'ulog':ulog,'n':len(actual)}
    row['odigrano']=evaluate(actual,leg)
    for mode in ('rasprseno','hibrid','slojevi'):
        rr=[evaluate(build(sizes,stakes,cnt,leg,mode,random.Random(sd)),leg) for sd in range(20)]
        row[mode]=tuple(st.mean(x[j] for x in rr) for j in range(3))
    perday.append(row)
    for k in ('odigrano','rasprseno','hibrid','slojevi'):
        w,p,rf=row[k]; T_=tot[k]; T_['w']+=w; T_['pay']+=p; T_['ref']+=rf; T_['ulog']+=ulog; T_['dani_sa_dobitkom']+= (w>=0.5 if k=='odigrano' else 0); T_['days']+=1
print('dan        kolo tiketa ulog  | odigrano (dobitnih/isplata) | raspršeno | hibrid | slojevi   (prosek 20 slaganja; isplata uključuje povraćaje)')
for r in perday:
    f=lambda k: f"{r[k][0]:.1f}/{r[k][1]:6.0f}"
    print(f"{r['dan']} {r['kolo']:>3} {r['n']:4d} {r['ulog']:6.0f} | {f('odigrano')} | {f('rasprseno')} | {f('hibrid')} | {f('slojevi')}")
print()
for k in ('odigrano','rasprseno','hibrid','slojevi'):
    T_=tot[k]; print(f"{k:10s}: dobitnih {T_['w']:.1f} | povraćaja {T_['ref']:.1f} | isplata {T_['pay']:.0f} od uloga {T_['ulog']} = {T_['pay']/T_['ulog']:.2f}")
for k in ('rasprseno','hibrid','slojevi'):
    d=sum(1 for r in perday if r[k][0]>=0.5); print(f"  {k}: dani sa bar pola dobitnog u proseku slaganja: {d}/{len(perday)}; dani u kojima je bar 1 slaganje od 20 dalo dobitak -> vidi gore")

print('nepotpunih tiketa (kraći od plana):',{k:f'{NEPOT[k]/NUK[k]:.1%}' for k in NUK})
