import json,collections,math
exec(open('/tmp/analiza24.py').read().split('# 1)')[0].replace('(131,132,133,134,135,136)','(137,138,139,140)'))
raw=open(E+'/baza/ponude/admiral/2026-11-25_opseg_poena.txt').read().strip().split(';')
rows=[]
for r in raw:
    ime,vr,op=r.split('|'); b=box(ime)
    for o in op.split(','):
        rr,k=o.split(':'); lo,hi=map(int,rr.split('-'))
        if not b or b['min']==0: continue
        rows.append((ime,rr,float(k),lo<=b['P']<=hi,b['P']))
hit=sum(r[3] for r in rows); ev=sum((r[2] if r[3] else 0)-1 for r in rows)
print('CELA PONUDA OPSEGA: %d opsega, prošlo %d (%.0f%%), ravnomerno %+.1f jed'%(len(rows),hit,100*hit/len(rows),ev))
P=json.load(open(E+'/minusi/arhiva/kola/r14d2/opseg_pool.json')); ours={(x['p'],x['r']) for x in P}
O=[r for r in rows if (r[0],r[1]) in ours]; h=sum(r[3] for r in O); e=sum((r[2] if r[3] else 0)-1 for r in O)
print('NAŠ IZBOR OPSEGA: %d, prošlo %d (%.0f%%), ravnomerno %+.1f jed'%(len(O),h,100*h/len(O),e))
print('  prošli:',[(r[0].split()[-1],r[1],r[2],r[4]) for r in O if r[3]])
lst=[('Mfiondu Kabengele','5-10'),('Cameron Payne','5-10'),('Carsen Edwards','15-20'),('Dario Šarić','10-15'),('Kobi Simmons','5-10'),('Azuolas Tubelis','5-10'),('Sasha Vezenkov','15-20'),('Dwayne Bacon','10-15'),('Tyson Ward','10-15'),('McKinley Wright IV','10-15'),('Chuma Okeke','5-10'),('Tyrique Jones','10-15')]
L=[r for r in rows if (r[0],r[1]) in lst]; print('LISTA 12: prošlo %d/%d, ravnomerno %+.1f jed'%(sum(r[3] for r in L),len(L),sum((r[2] if r[3] else 0)-1 for r in L)))
print('  ',[(r[0].split()[-1],r[1],r[4],'✓' if r[3] else '✗') for r in L])
T=json.load(open(E+'/minusi/planovi/plan_admiral_opseg_25_25nov.txt'))['tickets']+[{'legs':[{'p':'Mfiondu Kabengele','r':'5-10'},{'p':'Cameron Payne','r':'5-10'},{'p':'Carsen Edwards','r':'15-20'}]}]
res={(r[0],r[1]):r[3] for r in rows}
mc=collections.Counter(sum(1 for l in t['legs'] if not res.get((l['p'],l['r']),False)) for t in T)
print('TIKETI OPSEGA promašaji:',dict(sorted(mc.items())))
