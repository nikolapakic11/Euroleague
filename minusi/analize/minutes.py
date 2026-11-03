import json,numpy as np,collections
L=json.load(open('legs.json')); D=json.load(open('ds_all.json'))
E=[(0,12),(12,17),(17,21),(21,25),(25,45)]
print('PONUDA (svi ponudjeni minusi, 8 dana): minuta u sezoni pre utakmice')
for lo,hi in E:
    s=[d for d in D if lo<=d['pm']<hi]
    if not s: continue
    out=f'  {lo:2d}-{hi:2d} min: n={len(s):4d} prolaz {np.mean([d["hit"] for d in s]):.3f} (kvote kazu {np.mean([d["fair"] for d in s]):.3f})'
    for st in 'PSA':
        ss=[d for d in s if d['s']==st]
        if ss: out+=f' | {st} {np.mean([d["hit"] for d in ss]):.2f} n={len(ss)}'
    print(out)
print('ODIGRANO (jedinstveni parovi, sva kola od 2. kola):')
U={}
for l in L:
    if l['pm'] is None: continue
    U[(l['gday'],l['p'],l['stat'],l['line'])]=l
U=list(U.values())
for lo,hi in E:
    s=[l for l in U if lo<=l['pm']<hi]
    if not s: continue
    v=[l for l in s if l['res'] in('hit','miss')]
    big=[l for l in v if l['act_min'] and l['act_min']>1.3*l['pm']]
    out=f'  {lo:2d}-{hi:2d} min: parova {len(s):4d} prolaz {np.mean([l["res"]=="hit" for l in v]):.3f} nije igrao {np.mean([l["res"]=="void" for l in s]):.3f} prosecna kvota {np.mean([l["odds"] for l in s]):.2f} | igrao 30%+ vise minuta: {len(big)/max(1,len(v)):.2f} od parova, tada prolaz {np.mean([l["res"]=="hit" for l in big]) if big else 0:.2f}'
    for st in 'PSA':
        ss=[l for l in v if l['stat']==st]
        if ss: out+=f' | {st} {np.mean([l["res"]=="hit" for l in ss]):.2f} n={len(ss)}'
    print(out)
# placements
print('ODIGRANO po mestima na tiketima:')
for lo,hi in E:
    s=[l for l in L if l['pm'] is not None and lo<=l['pm']<hi and l['res'] in('hit','miss')]
    if s: print(f'  {lo:2d}-{hi:2d} min: mesta {len(s):4d} prolaz {np.mean([l["res"]=="hit" for l in s]):.3f}')
# starters vs bench in offer
print('Starter (startuje vecinu utakmica) vs klupa, ponuda:')
for lab,f in (('klupa',lambda d:d['st']<0.5),('starter',lambda d:d['st']>=0.5)):
    s=[d for d in D if f(d)]; print(f'  {lab}: n={len(s)} prolaz {np.mean([d["hit"] for d in s]):.3f}', ' '.join(f'{st} {np.mean([d["hit"] for d in s if d["s"]==st]):.2f}' for st in 'PSA'))
