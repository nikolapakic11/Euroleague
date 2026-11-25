exec(open('/tmp/ist.py').read().split("print('tiketa sa")[0])
import itertools,random,math,collections
rnd=random.Random(7)
for per,(a,b) in (('sve',('2026-09-01','2026-11-30')),('od 5.11.',('2026-11-05','2026-11-30'))):
    E=[(t,ss) for t,ss in T if len(t['legs'])==8 and a<=t['date']<=b]
    print(per,'osmice',len(E))
    for k in (4,5,6,8):
        cnt=win=0; ret=0.0
        for t,ss in E:
            nv=[(l,s) for l,s in zip(t['legs'],ss) if s!='v']
            if len(nv)<k: continue
            cs=list(itertools.combinations(nv,k))
            for c in (cs if len(cs)<=70 else rnd.sample(cs,70)):
                cnt+=1
                if all(s=='h' for l,s in c): win+=1; ret+=math.prod(l['odds'] for l,s in c)*(1+bon(k))
        print(f"   {k} od istih parova: dobitan 1 od {cnt/max(win,1):.0f} ({100*win/cnt:.2f}%), povraćaj bez povraćaja-promocije {ret/cnt-1:+.0%}")
