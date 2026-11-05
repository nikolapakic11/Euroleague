import json,re,unicodedata,math,collections,sys
B='/home/claude/euroleague/baza/ponude/'
pool=json.load(open('/home/claude/r10b/pool.json'))['pool']
adm=json.load(open(B+'admiral/2026-11-05_a.json'))
mb=json.load(open(B+'maxbet/2026-11-05_a.json'))['picks']
mz=json.load(open(B+'mozzart/2026-11-05_a.json'))['picks']
sb=json.load(open(B+'soccerbet/2026-11-05_a.json'))['picks']
H=open('/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html').read()
st=json.loads(re.search(r'<script type="application/json" id="state">(.*?)</script>',H,re.S).group(1))
TA=st['ctx2']['ta']; TM=adm['el']['tmap']; GK=list(json.load(open('/home/claude/r10b/lines.json'))['games'])
def game(code): return next(k for k in GK if code in k.split('-'))
def opp(code): g=game(code).split('-'); return g[1] if g[0]==code else g[0]
SUF={'jr','sr','ii','iii','iv'}
def nk(x):
    t=unicodedata.normalize('NFD',str(x or '')); t=''.join(ch for ch in t if unicodedata.category(ch)!='Mn').lower().replace('đ','dj')
    t=re.sub(r'[-.\']',' ',t); t=re.sub(r'[^a-z ]','',t); return [w for w in t.split() if w not in SUF]
def same(a,b):
    A,Bn=nk(a),nk(b)
    if not A or not Bn: return False
    return A[-1]==Bn[-1] and A[0][0]==Bn[0][0]
def fair(u,o): return (1/u)/((1/u)+(1/o))
def pois_cdf(k,m):
    s=0; t=math.exp(-m)
    for i in range(0,k+1):
        if i>0: t*=m/i
        s+=t
    return s
def shift(s,Lb,fb,L):
    if Lb==L: return fb
    if s=='P':
        sd=0.35*L+2.5; return fb+(L-Lb)*0.4/sd
    m=max(0.3,(L+Lb)/2)
    return fb+(pois_cdf(int(math.floor(L)),m)-pois_cdf(int(math.floor(Lb)),m))
def cons_for(p,s,L):
    out={}
    for name,book in (('maxbet',mb),('mozzart',mz),('soccerbet',sb)):
        c=[x for x in book if x.get('s')==s and same(x['p'],p) and x.get('u') and x.get('o')]
        if not c: continue
        ex=[x for x in c if x['l']==L]
        if ex: x=ex[0]; out[name]=(x['l'],round(fair(x['u'],x['o']),3))
        else:
            mm=[x for x in c if x.get('m',1)==1] or c
            x=min(mm,key=lambda x:abs(x['l']-L)); out[name]=(x['l'],round(min(0.95,max(0.05,shift(s,x['l'],fair(x['u'],x['o']),L))),3))
    return out
AP={(x['p'],x['s']):x for x in adm['picks']}
SN={'Poeni':'P','Skokovi':'S','Asistencije':'A'}
ALL=[]
for x in pool:
    s='P' if x['s'].startswith('Po') else 'S' if x['s'].startswith('Sk') else 'A'
    a=AP.get((x['p'],s))
    if not a: print('nema u ponudi',x['p'],s); continue
    code=TM.get(a['t']); g=game(code); oc=opp(code)
    pr0=x['pr']; adj=[]
    pr=pr0
    if s=='S' and TA.get(oc) and TA[oc][1]>=1.07: pr-=0.03; adj.append('protivnik dozvoljava mnogo skokova -3')
    if s=='A' and a['l']==1.5: pr-=0.03; adj.append('asistencije 1,5 -3')
    if s=='S' and a['l']==1.5: pr-=0.05; adj.append('skokovi 1,5 -5')
    cs=cons_for(a['p'],s,a['l']); af=fair(a['u'],a['o'])
    mk=None
    if cs:
        cv=sum(v[1] for v in cs.values())/len(cs); mk=cv-af
        d=max(-0.06,min(0.06,0.5*mk)); pr+=d
        if abs(d)>=0.01: adj.append(('ostale kladionice daju veću šansu minusu' if d>0 else 'ostale kladionice daju manju šansu minusu')+' %+d'%round(100*d))
    role=x['role']; cls='A' if role.startswith('više') else 'C' if role.startswith('malo') else 'B'
    ALL.append(dict(c=a['c'],p=a['p'],t=a['t'],s=s,l=a['l'],u=a['u'],o=a['o'],pr=round(pr,4),pr0=round(pr0,4),fair=round(af,3),g=g,time=a['time'],cls=cls,dim=x['dim'],role=role,cur=x['cur'],cons=cs,mk=None if mk is None else round(mk,3),adj=adj,unk='nepoznata' in role or 'još nije igrao' in x['cur']))
json.dump(ALL,open('/home/claude/r10b/all.json','w'),ensure_ascii=False)
print(len(ALL),'sa konsenzusom',sum(1 for x in ALL if x['cons']), 'po broju kladionica',collections.Counter(len(x['cons']) for x in ALL))
for x in sorted([x for x in ALL if not x['dim'] and not x['unk']],key=lambda x:-x['pr'])[:55]:
    print(f"{x['pr']:.3f} ({x['pr0']:.3f}) {x['p'][:22]:22s} {x['s']}{x['l']:<5} {x['u']:.2f} {x['g']} mk={x['mk']} {x['cons']} {x['adj']}")
