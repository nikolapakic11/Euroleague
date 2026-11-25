import json,collections,math,random
src=open('/tmp/analiza24.py').read().split('# 1)')[0]
E='/home/claude/Euroleague'
for dan,games,plan in (('20.11.',(127,128,129,130),'plan_admiral_60_20nov.txt'),('24.11.',(131,132,133,134,135,136),'plan_admiral_56_24nov.txt'),('25.11.',(137,138,139,140),'plan_admiral_65_25nov_odigrano.txt')):
    g={}; exec(src.replace('(131,132,133,134,135,136)',str(games)),g)
    T=json.load(open(f'{E}/minusi/planovi/{plan}'))['tickets']
    legs=[l for t in T for l in t['legs']]; res=[g['ishod'](l['p'],l['s'],l['l']) for l in legs]
    hit=sum(1 for r in res if r); tot=sum(1 for r in res if r is not None)
    iu=collections.Counter((l['p'],l['s'],l['l']) for l in legs); pu=collections.Counter(l['p'] for l in legs)
    N=len(T); sh=[c/len(legs) for c in iu.values()]; eff=1/sum(s*s for s in sh)
    top=sum(sorted(iu.values(),reverse=True)[:10])/len(legs)
    def mis(tk): return sum(1 for i in tk if res[i] is False)
    pos=0; act=collections.Counter()
    for t in T: act[mis(range(pos,pos+len(t['legs'])))]+=1; pos+=len(t['legs'])
    sizes=[len(t['legs']) for t in T]; rnd=random.Random(3); c0=[];c1=[]
    for _ in range(3000):
        idx=list(range(len(legs))); rnd.shuffle(idx); p=0; a=b=0
        for s in sizes:
            m=mis(idx[p:p+s]); p+=s; a+=m==0; b+=m==1
        c0.append(a); c1.append(b)
    # očekivano po binomu sa dnevnom stopom, po veličini tiketa
    q=hit/tot; e0=sum(q**s for s in sizes); e1=sum(s*(1-q)*q**(s-1) for s in sizes)
    print(f"{dan} tiketa {N}, parovi po mestima {hit}/{tot} = {100*q:.1f}% | stavka max {max(iu.values())} ({100*max(iu.values())/N:.0f}%), igrač max {max(pu.values())} ({100*max(pu.values())/N:.0f}%), efektivno stavki {eff:.0f}, top10 stavki {100*top:.0f}% mesta")
    print(f"      stvarno: čistih {act[0]}, sa 1 promašajem {act[1]}, sa 2 {act[2]} | nasumičan raspored istih parova: čistih {sum(c0)/len(c0):.2f}, sa 1 {sum(c1)/len(c1):.1f} | binom: čistih {e0:.2f}, sa 1 {e1:.1f}")
