import json,collections,sys
D='minusi/arhiva/kola/r14d2'
S=json.load(open(f'{D}/sel.json')); A=json.load(open(f'{D}/sel_sve.json'))
ins={(x['p'],x['s']) for x in S}
FT={'Real Madrid','Baskonia','Partizan'}
cap=float(sys.argv[1]) if len(sys.argv)>1 else 1.3; ime=sys.argv[2] if len(sys.argv)>2 else 'v1'
for x in A: x['mix']=round((x['pr']+1-x['pm'])/2 if x.get('pm') is not None else x['pr'],4)
def iw(x):
    m=x['mix']
    if (x['p'],x['s']) not in ins:
        return .45 if (x['t'] in FT and m>=.58) else 0
    return 1.0 if m>=.62 else .85 if m>=.58 else .7 if m>=.54 else .5 if m>=.50 else 0
pool=[];tez=collections.defaultdict(list);rows=[]
for x in A:
    if x['u']<1.60: continue
    w=iw(x)
    if w<=0: continue
    z=dict(x); z['pr']=x['mix']; pool.append(z); tez[x['p']].append(w); rows.append((x['mix'],x['p'],x['s'],x['l'],x['u'],x['g'],w))
FTP={x['p'] for x in pool}-{p for p,s in ins}
tez={p:(0.25 if p in FTP else round(min(max(max(v)+0.1*(len(v)-1),.5),cap),3)) for p,v in tez.items()}
json.dump(pool,open(f'{D}/sel_{ime}.json','w'),ensure_ascii=False); json.dump(tez,open(f'{D}/tez_{ime}.json','w'),ensure_ascii=False)
print(ime,'stavki',len(pool),'igrača',len(tez),'po utakmici',dict(collections.Counter(x['g'] for x in pool)), 'igrača po utakmici',dict(collections.Counter(x['g'] for x in {(z['p'],z['g']):z for z in pool}.values())))
print('zbir težina',round(sum(tez.values()),1), 'raspon',min(tez.values()),max(tez.values()))
if '-v' in sys.argv:
    for r in sorted(rows,reverse=True): print('  %.3f %-24s %s u%-5s @%-5s %s w%.1f'%r)
