"""Provera izbora za sajt i novih signala (13.11.2026).
  python3 spoj/analiza/an3.py
Radi nad spoj/analiza/F.json (posle provera.py + prep.py). Sve procene su „bez tog kola“ (uči na ostalim kolima)."""
import json, math, os, sys, collections, statistics as st
import numpy as np
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))); os.chdir(R); sys.path.insert(0, R + '/spoj')
import signali
from signali import lgt, osobine
sg = lambda z: 1 / (1 + math.exp(-z))
FA = json.load(open('spoj/analiza/F.json'))
rows = signali.Signali().B.rows
byk = collections.defaultdict(list); byteam = collections.defaultdict(lambda: collections.defaultdict(list))
for r in rows:
    byk[r['k']].append(r); byteam[r['team']][r['dan']].append(r)
for v in byk.values(): v.sort(key=lambda r: r['dan'])
lg = collections.defaultdict(list)                       # liga: stavka po minutu po poziciji
for r in rows:
    if r['min'] > 0:
        for s in 'PSA': lg[(r['pos'], s)].append((r['dan'], r[s], r['min']))
def dozv(opp, dan, pos, s):
    """Koliko protivnik dozvoljava igračima te pozicije (po minutu) prema ligi, samo utakmice pre dana."""
    a = b = 0
    for t, D in byteam.items():
        for d, L in D.items():
            if d < dan:
                for r in L:
                    if r['opp'] == opp and r['pos'] == pos and r['min'] > 0: a += r[s]; b += r['min']
    la = sum(v for d, v, m in lg[(pos, s)] if d < dan); lb = sum(m for d, v, m in lg[(pos, s)] if d < dan)
    return (a / b) / (la / lb) if b > 150 and lb else 1.0
tempo = {}
def tm_tempo(team, dan):
    key = (team, dan)
    if key not in tempo:
        v = []
        for d, L in byteam[team].items():
            if d < dan:
                opp = L[0]['opp']; v.append(sum(r['P'] for r in L) + sum(r['P'] for r in byteam[opp].get(d, [])))
        tempo[key] = sum(v) / len(v) if v else 165
    return tempo[key]
from datetime import date
dd = lambda a, b: (date.fromisoformat(a) - date.fromisoformat(b)).days
for x in FA:
    g = [r for r in byk[x['k']] if r['dan'] < x['dan'] and r['min'] > 0]
    mn = [r['min'] for r in g]
    x['minsd'] = st.pstdev(mn) if len(mn) > 2 else 5.0
    l5 = g[-5:]; x['emp5'] = (sum(1 for r in l5 if r[x['s']] < x['l']) + 1) / (len(l5) + 2)
    td = sorted(d for d in byteam[x['team']] if d < x['dan'])
    x['propusteno'] = 0                                   # koliko je utakmica tima igrač propustio neposredno pre ove
    for d in reversed(td):
        if any(r['k'] == x['k'] and r['min'] > 0 for r in byteam[x['team']][d]): break
        x['propusteno'] += 1
    x['dozv'] = dozv(x['opp'], x['dan'], x['pos'], x['s'])
    x['tempo'] = (tm_tempo(x['team'], x['dan']) + tm_tempo(x['opp'], x['dan'])) / 2
    x['st_last'] = (g[-1]['st'] if g else 0) - x['st']
    x['lean'] = (1 / x['u']) / (1 / x['u'] + 1 / x['o'])   # tržišna verovatnoća ispod
    x['perm'] = x['avg'] / max(x['am'], 5)
    x['X'] = osobine(x['pm'], x['tr'], x['msig'], x['missmin'], x['zline'], x['s'], x['l']); x['Lq'] = lgt(1 - x['tr'])
    x['gk'] = '-'.join(sorted((x['team'], x['opp'])))
MV = {(m['bk'], m['dan'], m['k'], m['s']): m for m in json.load(open('spoj/analiza/MV.json'))}
for x in FA:
    m = MV.get((x['izvor'], x['dan'], x['k'], x['s']))
    x['dl'] = (m['l1'] - m['l0']) if m else None; x['df'] = (m['f1'] - m['f0']) if m else None
F = [x for x in FA if x['izvor'] == 'admiral']
kola = sorted({x['kolo'] for x in F})


def uci(Rr, FE, lam=2.0):
    mean = {f: st.mean(x['X'][f] for x in Rr) for f in FE}; sd = {f: st.pstdev(x['X'][f] for x in Rr) or 1 for f in FE}
    X = np.array([[1] + [(x['X'][f] - mean[f]) / sd[f] for f in FE] for x in Rr]); y = np.array([x['y'] for x in Rr], float); off = np.array([x['Lq'] for x in Rr])
    w = np.zeros(X.shape[1])
    for _ in range(80):
        p = 1 / (1 + np.exp(-(off + X @ w))); g = X.T @ (p - y) + lam * np.r_[0, w[1:]]
        H = (X.T * (p * (1 - p))) @ X + lam * np.diag(np.r_[0, np.ones(len(w) - 1)]); w -= np.linalg.solve(H, g)
    return dict(FE=FE, mean=mean, sd=sd, w=dict(zip(FE, map(float, w[1:]))), b=float(w[0]))
pr = lambda T, x: sg(x['Lq'] + T['b'] + sum(T['w'][f] * (x['X'][f] - T['mean'][f]) / T['sd'][f] for f in T['FE']))
BASE = ['pu', 'ms', 'mm', 'zl', 'pmid']


def loro(FE, key, lam=2.0, skup=F):
    for k in kola:
        T = uci([x for x in skup if x['kolo'] != k], FE, lam)
        for x in FA:
            if x['kolo'] == k: x[key] = pr(T, x)
loro(BASE, 'p2')


def rep(S, strana='u'):
    if not S: return 'n=0'
    h = sum(x['y'] if strana == 'u' else 1 - x['y'] for x in S); n = len(S)
    roi = sum(((x[strana] - 1) if (x['y'] if strana == 'u' else 1 - x['y']) else -1) for x in S) / n
    return f"{h / n:5.1%} (n={n:3}, kv {sum(x[strana] for x in S) / n:.2f}, povr {roi:+.1%})"


def vrhN(score, N, strana='u', po_ut=2, minu=1.60, skup=F, uslov=lambda x: True):
    """N najboljih po danu: jedan po igraču, najviše po_ut po utakmici, kvota bar minu."""
    out = []; byd = collections.defaultdict(list)
    for x in skup:
        if x[strana] >= minu and uslov(x): byd[x['dan']].append(x)
    for d, L in byd.items():
        L = sorted(L, key=lambda x: -score(x)); iz = []
        for x in L:
            if len(iz) >= N: break
            if all(q['k'] != x['k'] for q in iz) and sum(q['gk'] == x['gk'] for q in iz) < po_ut: iz.append(x)
        out += iz
    return out
print('=== 1. ISPOD: N najboljih po danu, razni načini rangiranja (Admiral, kola %d–%d, %d dana) ===' % (kola[0], kola[-1], len({x['dan'] for x in F})))
print('sve Admiral granice ispod, kvota ≥1,60:', rep([x for x in F if x['u'] >= 1.6]))
NACINI = [('spoj: verovatnoća × kvota', lambda x: x['p2'] * x['u']), ('spoj: verovatnoća', lambda x: x['p2']),
          ('samo procene (1−pm)', lambda x: 1 - x['pm']), ('procene prednost (tr−pm)', lambda x: x['tr'] - x['pm']),
          ('samo minus-model (msig)', lambda x: x['msig']), ('tržište (najniža kvota)', lambda x: -x['u'])]
for nm, sc in NACINI:
    print(f"  {nm:28} top4 {rep(vrhN(sc, 4))} | top8 {rep(vrhN(sc, 8))} | top15 {rep(vrhN(sc, 15, po_ut=4))}")
print('  sajt-pravilo (procene prednost + msig≥0,35):', 'top4', rep(vrhN(lambda x: x['tr'] - x['pm'], 4, uslov=lambda x: x['msig'] >= .35 and 1 - x['pm'] >= .54)),
      '| top8', rep(vrhN(lambda x: x['tr'] - x['pm'], 8, uslov=lambda x: x['msig'] >= .35 and 1 - x['pm'] >= .54)))
print('  po stavci, spoj vrednost top8:', {s: rep([x for x in vrhN(lambda x: x['p2'] * x['u'], 8) if x['s'] == s]) for s in 'PSA'})
print('\n=== 2. Ostatak (ishod − spoj) po novim signalima, sve Admiral granice; + znači češće ISPOD nego što spoj misli ===')
SIG = ['mintrend', 'hot', 'rest', 'dom', 'mdiff', 'st', 'am', 'rang', 'retmin', 'mcv', 'n', 'emp', 'emp5', 'minsd', 'propusteno', 'dozv', 'tempo', 'st_last', 'lean', 'perm', 'ldev', 'nbk', 'dl', 'df', 'l', 'u']
for f in SIG:
    L = sorted([x for x in F if x.get(f) is not None], key=lambda x: x[f]); n = len(L)
    if n < 150: print(f"  {f:10} premalo ({n})"); continue
    T3 = [L[:n // 3], L[n // 3:2 * n // 3], L[2 * n // 3:]]
    res = [sum(x['y'] - x['p2'] for x in t) / len(t) for t in T3]
    # po polovinama kola: stabilnost znaka
    stab = []
    for kk in (kola[:len(kola) // 2], kola[len(kola) // 2:]):
        Lk = [x for x in L if x['kolo'] in kk]; m = len(Lk)
        stab.append(sum(x['y'] - x['p2'] for x in Lk[2 * m // 3:]) / max(1, m - 2 * m // 3) - sum(x['y'] - x['p2'] for x in Lk[:m // 3]) / max(1, m // 3))
    print(f"  {f:10} n{n:5} donja {res[0]:+.3f} srednja {res[1]:+.3f} gornja {res[2]:+.3f} | gornja−donja: prva pol. {stab[0]:+.3f}, druga pol. {stab[1]:+.3f}  [{L[n // 3][f]:.2f} / {L[2 * n // 3][f]:.2f}]")

print('\n=== 3. Prošireni spoj: + trend minuta, forma, tempo, kolebanje minuta, odmor ===')
clip = lambda v, a, b: max(a, min(b, v))
for x in FA:
    x['X'].update(mt=clip(x['mintrend'], -8, 8), hot=clip(x['hot'], -2, 2), tempo=clip(x['tempo'], 150, 190), minsd=clip(x['minsd'], 0, 10), rest=clip(x['rest'], 1, 8), emp5=x['emp5'])
VAR = {'p2': BASE, 'p3 (+mt,hot,tempo,minsd)': BASE + ['mt', 'hot', 'tempo', 'minsd'], 'p4 (+rest)': BASE + ['mt', 'hot', 'tempo', 'minsd', 'rest'], 'p5 (+mt,tempo)': BASE + ['mt', 'tempo']}
ll = lambda key, S: -sum(math.log(x[key] if x['y'] else 1 - x[key]) for x in S) / len(S)
for key, FE in VAR.items():
    k0 = key.split()[0]
    loro(FE, k0)
    print(f"  {key:28} logloss {ll(k0, F):.4f} | po verovatnoći: top4 {rep(vrhN(lambda x: x[k0], 4))} | top8 {rep(vrhN(lambda x: x[k0], 8))} | top15 {rep(vrhN(lambda x: x[k0], 15, po_ut=4))}")
    print(f"  {'':28} po vrednosti:   top8 {rep(vrhN(lambda x: x[k0] * x['u'], 8))} | top15 {rep(vrhN(lambda x: x[k0] * x['u'], 15, po_ut=4))} | top30 {rep(vrhN(lambda x: x[k0] * x['u'], 30, po_ut=8))}")
print('  težine p3 (sva kola):', {f: round(v, 3) for f, v in uci(F, VAR['p3 (+mt,hot,tempo,minsd)'])['w'].items()})
print('  strogo unapred (uči samo na ranijim kolima), kola 8+:')
for key, FE in (('f2', BASE), ('f3', VAR['p3 (+mt,hot,tempo,minsd)'])):
    for k in [k for k in kola if k >= 8]:
        T = uci([x for x in F if x['kolo'] < k], FE)
        for x in FA:
            if x['kolo'] == k: x[key] = pr(T, x)
    S8 = [x for x in F if x['kolo'] >= 8]
    print(f"    {key}: logloss {ll(key, S8):.4f} | po verovatnoći top4 {rep(vrhN(lambda x: x[key], 4, skup=S8))} | top8 {rep(vrhN(lambda x: x[key], 8, skup=S8))} | po vrednosti top15 {rep(vrhN(lambda x: x[key] * x['u'], 15, po_ut=4, skup=S8))}")
print('  po stavci (p3, po verovatnoći, top8):', {s: rep([x for x in vrhN(lambda x: x['p3'], 8) if x['s'] == s]) for s in 'PSA'})
print('  po kolu (p3, po verovatnoći, top4):', {k: rep([x for x in vrhN(lambda x: x['p3'], 4) if x['kolo'] == k])[:5] for k in kola})
print('\n=== 4. Kretanje granice u toku dana (Admiral, prvi → poslednji snimak) ===')
M = [x for x in F if x['dl'] is not None]
for nm, f in (('granica podignuta', lambda x: x['dl'] > 0), ('granica ista', lambda x: x['dl'] == 0), ('granica spuštena', lambda x: x['dl'] < 0)):
    S = [x for x in M if f(x)]
    if S: print(f"  {nm:18} n{len(S):4} ispod (na poslednjoj granici) {sum(x['y'] for x in S) / len(S):.1%}, spoj očekuje {sum(x['p2'] for x in S) / len(S):.1%}")
S0 = [x for x in M if x['dl'] == 0]
for nm, f in (('kvota na ispod pala (tržište ide ka ispod)', lambda x: x['df'] < -0.015), ('bez promene', lambda x: abs(x['df']) <= 0.015), ('kvota na preko pala (tržište ide ka preko)', lambda x: x['df'] > 0.015)):
    S = [x for x in S0 if f(x)]
    if S: print(f"  ista granica, {nm:42} n{len(S):4} ispod {sum(x['y'] for x in S) / len(S):.1%}, spoj očekuje {sum(x['p2'] for x in S) / len(S):.1%}")
print('\n=== 5. PREKO ===')
print('  sve Admiral granice preko, kvota ≥1,60:', rep([x for x in F if x['o'] >= 1.6], 'o'))
PL = [('spoj p3: verovatnoća preko', lambda x: 1 - x['p3']), ('spoj p3: vrednost', lambda x: (1 - x['p3']) * x['o']), ('procene pm', lambda x: x['pm']), ('procene prednost pm−tr', lambda x: x['pm'] - x['tr']), ('minus-model obrnuto', lambda x: -x['msig'])]
for nm, sc in PL:
    print(f"  {nm:28} top1 {rep(vrhN(sc, 1, 'o'), 'o')} | top2 {rep(vrhN(sc, 2, 'o'), 'o')} | top4 {rep(vrhN(sc, 4, 'o'), 'o')} | top8 {rep(vrhN(sc, 8, 'o'), 'o')}")
print('  samo poeni/asistencije, p3 verovatnoća: top2', rep(vrhN(lambda x: 1 - x['p3'], 2, 'o', uslov=lambda x: x['s'] in 'PA'), 'o'), '| top4', rep(vrhN(lambda x: 1 - x['p3'], 4, 'o', uslov=lambda x: x['s'] in 'PA'), 'o'))
USL = [('izostanci ≥40, P/A, pm>tr, pm≥0,5 (pravilo od 12.11.)', lambda x: x['missmin'] >= 40 and x['s'] in 'PA' and x['pm'] > x['tr'] and x['pm'] >= .5),
       ('isto + igrač u posl. 3 igrao ≥15 min u proseku', lambda x: x['missmin'] >= 40 and x['s'] in 'PA' and x['pm'] > x['tr'] and x['pm'] >= .5 and x['am'] + x['mintrend'] >= 15),
       ('minuti u padu (mintrend ≤ −3)', lambda x: x['mintrend'] <= -3), ('hladan (hot ≤ −0,5)', lambda x: x['hot'] <= -.5),
       ('granica ispod proseka (zline ≤ −0,3)', lambda x: x['zline'] <= -.3), ('zline ≤ −0,3 i izostanci ≥ 25', lambda x: x['zline'] <= -.3 and x['missmin'] >= 25),
       ('zline ≤ −0,3 i pm ≥ 0,5', lambda x: x['zline'] <= -.3 and x['pm'] >= .5), ('spoj p3 preko ≥ 0,55', lambda x: 1 - x['p3'] >= .55), ('spoj p3 preko ≥ 0,58', lambda x: 1 - x['p3'] >= .58),
       ('spoj p3 preko ≥ 0,55 i P/A', lambda x: 1 - x['p3'] >= .55 and x['s'] in 'PA'), ('granica spuštena u toku dana', lambda x: x['dl'] is not None and x['dl'] < 0), ('granica podignuta u toku dana', lambda x: x['dl'] is not None and x['dl'] > 0)]
for nm, f in USL:
    S = [x for x in F if x['o'] >= 1.6 and f(x)]
    h1 = [x for x in S if x['kolo'] <= 7]; h2 = [x for x in S if 8 <= x['kolo'] <= 10]; h3 = [x for x in S if x['kolo'] == 11]
    print(f"  {nm:52} {rep(S, 'o')} | kola 4-7 {rep(h1, 'o')[:5]} n{len(h1)} | 8-10 {rep(h2, 'o')[:5]} n{len(h2)} | 11 {rep(h3, 'o')[:5]} n{len(h3)}")
print('\n=== 6. Kako bi izgledao sajt: 4 ISPOD po verovatnoći (p3) + PLUS ===')
U4 = vrhN(lambda x: x['p3'], 4)
dn = collections.defaultdict(list)
for x in U4: dn[x['dan']].append(x['y'])
print('  ispod: ', rep(U4), '| dana sa bar 3 od 4:', sum(1 for v in dn.values() if sum(v) >= 3), 'od', len(dn), '| dana sa 2:', sum(1 for v in dn.values() if sum(v) == 2), '| dana sa ≤1:', sum(1 for v in dn.values() if sum(v) <= 1))

print('\n=== 7. Dodatne provere ===')
H1 = set(kola[:len(kola) // 2]); H2 = set(kola) - H1
for s_ in 'PSA':
    T15 = [x for x in vrhN(lambda x: x['p3'], 15, po_ut=4) if x['s'] == s_]; T30 = [x for x in vrhN(lambda x: x['p3'], 40, po_ut=10) if x['s'] == s_]
    print(f"  ISPOD {s_}: top15/dan {rep(T15)} [prva pol. {rep([x for x in T15 if x['kolo'] in H1])[:5]}, druga {rep([x for x in T15 if x['kolo'] in H2])[:5]}] | top40/dan {rep(T30)} | sve {rep([x for x in F if x['s'] == s_ and x['u'] >= 1.6])}")
for nm, usl in (('bez skokova', lambda x: x['s'] != 'S'), ('skokovi samo ako p3 ≥ 0,66', lambda x: x['s'] != 'S' or x['p3'] >= .66), ('skokovi najviše 1', None)):
    if usl:
        T = vrhN(lambda x: x['p3'], 4, uslov=usl); T8 = vrhN(lambda x: x['p3'], 8, uslov=usl)
        print(f"  ISPOD top4 {nm:26} {rep(T)} | top8 {rep(T8)}")
for key in ('p2', 'p3'):
    for nm, usl in (('sve stavke', lambda x: True), ('P/A', lambda x: x['s'] in 'PA')):
        T1 = vrhN(lambda x: 1 - x[key], 1, 'o', uslov=usl); T2 = vrhN(lambda x: 1 - x[key], 2, 'o', uslov=usl); T3 = vrhN(lambda x: 1 - x[key], 3, 'o', uslov=usl)
        print(f"  PREKO {key} {nm:10} top1 {rep(T1, 'o')[:5]} [{rep([x for x in T1 if x['kolo'] in H1], 'o')[:5]} / {rep([x for x in T1 if x['kolo'] in H2], 'o')[:5]}] | top2 {rep(T2, 'o')} [{rep([x for x in T2 if x['kolo'] in H1], 'o')[:5]} / {rep([x for x in T2 if x['kolo'] in H2], 'o')[:5]}] | top3 {rep(T3, 'o')[:13]}")
for key in ('f2', 'f3'):
    S8 = [x for x in F if x['kolo'] >= 8]
    print(f"  PREKO strogo unapred {key} kola 8+: P/A top1 {rep(vrhN(lambda x: 1 - x[key], 1, 'o', skup=S8, uslov=lambda x: x['s'] in 'PA'), 'o')} | top2 {rep(vrhN(lambda x: 1 - x[key], 2, 'o', skup=S8, uslov=lambda x: x['s'] in 'PA'), 'o')} | prag ≥0,55 P/A {rep([x for x in S8 if x['o'] >= 1.6 and x['s'] in 'PA' and 1 - x[key] >= .55], 'o')}")
for pr_ in (.52, .55, .58, .60):
    T = vrhN(lambda x: 1 - x['p3'], 2, 'o', uslov=lambda x: x['s'] in 'PA' and 1 - x['p3'] >= pr_)
    print(f"  PREKO P/A top2 uz prag {pr_}: {rep(T, 'o')} dana {len({x['dan'] for x in T})}")
print('  šta gura PREKO (prosek osobina, top2 P/A prema svima):', {f: (round(st.mean(x['X'][f] for x in vrhN(lambda x: 1 - x['p3'], 2, 'o', uslov=lambda x: x['s'] in 'PA')), 2), round(st.mean(x['X'][f] for x in F), 2)) for f in ('pu', 'ms', 'mm', 'zl', 'mt', 'hot')})
MVA = json.load(open('spoj/analiza/MV.json'))
print('  Kretanje, sve četiri kladionice (ishod prema poslednjoj granici):')
def mrep(S):
    if not S: return 'n=0'
    ov = sum(1 for m in S if m['act'] > m['l1']); n = len(S)
    return f"n{n:4} preko {ov / n:.1%} (povr preko {sum((m['o1'] - 1) if m['act'] > m['l1'] else -1 for m in S) / n:+.1%}, povr ispod {sum((m['u1'] - 1) if m['act'] < m['l1'] else -1 for m in S) / n:+.1%})"
for nm, f in (('granica podignuta', lambda m: m['l1'] > m['l0']), ('granica spuštena', lambda m: m['l1'] < m['l0']), ('ista, tržište ka preko (≥1,5 pp)', lambda m: m['l1'] == m['l0'] and m['f1'] - m['f0'] >= .015),
              ('ista, tržište ka preko (≥3 pp)', lambda m: m['l1'] == m['l0'] and m['f1'] - m['f0'] >= .03), ('ista, tržište ka ispod (≥1,5 pp)', lambda m: m['l1'] == m['l0'] and m['f1'] - m['f0'] <= -.015), ('ista, bez promene', lambda m: m['l1'] == m['l0'] and abs(m['f1'] - m['f0']) < .015)):
    S = [m for m in MVA if f(m)]
    print(f"    {nm:34} {mrep(S)} | bez Admirala {mrep([m for m in S if m['bk'] != 'admiral'])[:20]}")
d12 = '2026-11-12'
print('  12.11. po novom izboru: ISPOD', [(x['k'], x['s'], x['l'], x['u'], round(x['p3'], 2), 'prošao' if x['y'] else 'pao') for x in vrhN(lambda x: x['p3'], 4) if x['dan'] == d12])
print('  12.11. PREKO P/A', [(x['k'], x['s'], x['l'], x['o'], round(1 - x['p3'], 2), 'prošao' if not x['y'] else 'pao') for x in vrhN(lambda x: 1 - x['p3'], 2, 'o', uslov=lambda x: x['s'] in 'PA') if x['dan'] == d12])
print('  11.11. ISPOD', [(x['k'], x['s'], x['l'], round(x['p3'], 2), 'prošao' if x['y'] else 'pao') for x in vrhN(lambda x: x['p3'], 4) if x['dan'] == '2026-11-11'], 'PREKO', [(x['k'], x['s'], x['l'], round(1 - x['p3'], 2), 'prošao' if not x['y'] else 'pao') for x in vrhN(lambda x: 1 - x['p3'], 2, 'o', uslov=lambda x: x['s'] in 'PA') if x['dan'] == '2026-11-11'])

print('\n=== 8. Pravila za sajt (p3) ===')
def vrhS(N, maxS=1, uslov=lambda x: True, po_tim=2, po_ut=2, key='p3'):
    out = []; byd = collections.defaultdict(list)
    for x in F:
        if x['u'] >= 1.6 and uslov(x): byd[x['dan']].append(x)
    for d, L in byd.items():
        iz = []
        for x in sorted(L, key=lambda x: -x[key]):
            if len(iz) >= N: break
            if all(q['k'] != x['k'] for q in iz) and sum(q['gk'] == x['gk'] for q in iz) < po_ut and sum(q['team'] == x['team'] for q in iz) < po_tim and (x['s'] != 'S' or sum(q['s'] == 'S' for q in iz) < maxS): iz.append(x)
        out += iz
    return out
def dani(T, strana='u'):
    dn = collections.defaultdict(list)
    for x in T: dn[x['dan']].append(x['y'] if strana == 'u' else 1 - x['y'])
    return f"dana ≥75%: {sum(1 for v in dn.values() if sum(v) / len(v) >= .75)}, 50%: {sum(1 for v in dn.values() if sum(v) / len(v) == .5)}, <50%: {sum(1 for v in dn.values() if sum(v) / len(v) < .5)}"
for nm, kw in (('top4, skokovi ≤1', dict(N=4)), ('top4, skokovi ≤1, msig≥0,35', dict(N=4, uslov=lambda x: x['msig'] >= .35)), ('top4, skokovi ≤1, forma5 ≥ 0,5', dict(N=4, uslov=lambda x: x['emp5'] >= .5)),
               ('top4, skokovi ≤1, kvota ≥1,70', dict(N=4, uslov=lambda x: x['u'] >= 1.7)), ('top5, skokovi ≤1', dict(N=5)), ('top6, skokovi ≤2', dict(N=6, maxS=2)), ('top4, skokovi ≤1, izostanci <35', dict(N=4, uslov=lambda x: x['missmin'] < 35)),
               ('top4 po p2, skokovi ≤1', dict(N=4, key='p2'))):
    T = vrhS(**kw); print(f"  ISPOD {nm:34} {rep(T)} | prosečna procena {sum(x[kw.get('key', 'p3')] for x in T) / len(T):.1%} | {dani(T)}")
for b0, b1 in ((.5, .55), (.55, .6), (.6, .65), (.65, .7), (.7, 1)):
    S = [x for x in F if b0 <= x['p3'] < b1 and x['u'] >= 1.6]; print(f"  kalibracija ISPOD p3 {b0}-{b1}: n{len(S):4} stvarno {sum(x['y'] for x in S) / max(1, len(S)):.1%}")
for b0, b1 in ((.5, .55), (.55, .6), (.6, .65), (.65, 1)):
    S = [x for x in F if b0 <= 1 - x['p3'] < b1 and x['o'] >= 1.6]; print(f"  kalibracija PREKO p3 {b0}-{b1}: n{len(S):4} stvarno {sum(1 - x['y'] for x in S) / max(1, len(S)):.1%} | P/A {sum(1 - x['y'] for x in S if x['s'] in 'PA') / max(1, sum(1 for x in S if x['s'] in 'PA')):.1%} n{sum(1 for x in S if x['s'] in 'PA')}")
def vrhO(N, uslov, key='p3'):
    out = []; byd = collections.defaultdict(list)
    for x in F:
        if x['o'] >= 1.6 and x['s'] in 'PA' and uslov(x): byd[x['dan']].append(x)
    for d, L in byd.items():
        iz = []
        for x in sorted(L, key=lambda x: x[key]):
            if len(iz) >= N: break
            if all(q['k'] != x['k'] for q in iz) and sum(q['team'] == x['team'] for q in iz) < 1: iz.append(x)
        out += iz
    return out
for nm, N, u in (('top1', 1, lambda x: True), ('top2, jedan po timu', 2, lambda x: True), ('top2, prag 0,58', 2, lambda x: 1 - x['p3'] >= .58), ('top2, pm ≥ 0,45', 2, lambda x: x['pm'] >= .45), ('top2, izostanci ≥ 25', 2, lambda x: x['missmin'] >= 25),
                 ('top2, minuti posl.3 ≥ 15', 2, lambda x: x['am'] + x['mintrend'] >= 15), ('top2, kvota ≥ 1,70', 2, lambda x: x['o'] >= 1.7), ('top3', 3, lambda x: True)):
    T = vrhO(N, u); print(f"  PREKO P/A {nm:26} {rep(T, 'o')} | prosečna procena {sum(1 - x['p3'] for x in T) / len(T):.1%} | {dani(T, 'o')}")
T = vrhS(4) + vrhO(2, lambda x: True)
dn = collections.defaultdict(list)
for x in vrhS(4): dn[x['dan']].append(x['y'])
for x in vrhO(2, lambda x: True): dn[x['dan']].append(1 - x['y'])
print('  SAJT ukupno (4 ispod + 2 preko):', f"{sum(sum(v) for v in dn.values())}/{sum(len(v) for v in dn.values())} = {sum(sum(v) for v in dn.values()) / sum(len(v) for v in dn.values()):.1%}", '| po danu:', sorted(f"{sum(v)}/{len(v)}" for v in dn.values()))

print('\n=== 9. Konačno pravilo za sajt ===')
U = lambda x: x['msig'] >= .35 and x['missmin'] < 35
T = vrhS(4, uslov=U); print('  ISPOD (top4 po verovatnoći, msig≥0,35, izostanci<35, skokovi ≤1):', rep(T), '|', dani(T), '| po polovinama', rep([x for x in T if x['kolo'] in H1])[:5], rep([x for x in T if x['kolo'] in H2])[:5], '| po stavci', {s_: rep([x for x in T if x['s'] == s_])[:13] for s_ in 'PSA'})
S8 = [x for x in F if x['kolo'] >= 8]
def vrhS8(key):
    out = []; byd = collections.defaultdict(list)
    for x in S8:
        if x['u'] >= 1.6 and U(x): byd[x['dan']].append(x)
    for d, L in byd.items():
        iz = []
        for x in sorted(L, key=lambda x: -x[key]):
            if len(iz) >= 4: break
            if all(q['k'] != x['k'] for q in iz) and sum(q['gk'] == x['gk'] for q in iz) < 2 and (x['s'] != 'S' or sum(q['s'] == 'S' for q in iz) < 1): iz.append(x)
        out += iz
    return out
print('  isto, strogo unapred kola 8+: f2', rep(vrhS8('f2')), '| f3', rep(vrhS8('f3')))
O1 = vrhO(1, lambda x: 1 - x['p3'] >= .55); O2 = [x for x in vrhO(2, lambda x: 1 - x['p3'] >= .65) if x not in O1]
print('  PREKO (P/A, najbolji po danu uz ≥0,55; drugi samo uz ≥0,65):', rep(O1 + O2, 'o'), '| prvi', rep(O1, 'o')[:13], '| drugi', rep(O2, 'o')[:13])
dn = collections.defaultdict(list)
for x in T: dn[x['dan']].append(x['y'])
for x in O1 + O2: dn[x['dan']].append(1 - x['y'])
tot = sum(sum(v) for v in dn.values()); nn = sum(len(v) for v in dn.values())
print(f"  SAJT ukupno: {tot}/{nn} = {tot / nn:.1%} | dana iznad 50%: {sum(1 for v in dn.values() if sum(v) / len(v) > .5)} od {len(dn)}, tačno 50%: {sum(1 for v in dn.values() if sum(v) / len(v) == .5)}, ispod: {sum(1 for v in dn.values() if sum(v) / len(v) < .5)}")
print('  staro pravilo sajta (procene prednost, msig≥0,35, pm ispod ≥0,54), top4:', rep(vrhN(lambda x: x['tr'] - x['pm'], 4, uslov=lambda x: x['msig'] >= .35 and 1 - x['pm'] >= .54)), '| PREKO po prednosti procena top1', rep(vrhN(lambda x: x['pm'] - x['tr'], 1, 'o'), 'o'))
json.dump([{k: v for k, v in x.items() if k != 'X'} for x in FA], open('/tmp/F3.json', 'w'))
if '--dan' in sys.argv:
    d_ = sys.argv[sys.argv.index('--dan') + 1]
    print('\n=== izbor po konačnom pravilu za', d_, '===')
    for x in sorted([x for x in F if x['dan'] == d_ and x['u'] >= 1.6], key=lambda x: -x['p3'])[:14]:
        print(f"  {x['k'][:22]:22} {x['s']} {x['l']:5} u{x['u']:5} p3 {x['p3']:.3f} p2 {x['p2']:.3f} tr_ispod {1 - x['tr']:.3f} pm_preko {x['pm']:.3f} msig {x['msig']:+.2f} fali {x['missmin']:.0f} zl {x['zline']:+.2f} mt {x['mintrend']:+.1f} {'U IZBORU' if x in T else ''} -> {'prošao' if x['y'] else 'pao'} ({x['act']})")
if '--oblik' in sys.argv:
    print('\n=== oblik novih signala (logloss: bez tog kola | strogo unapred kola 8+) ===')
    S8 = [x for x in F if x['kolo'] >= 8]
    def proba(nm, FE, prip):
        for x in FA: prip(x)
        loro(FE, 'pt')
        for k in [k for k in kola if k >= 8]:
            T_ = uci([x for x in F if x['kolo'] < k], FE)
            for x in FA:
                if x['kolo'] == k: x['ft'] = pr(T_, x)
        t4 = vrhS(4, uslov=U, key='pt'); t8 = vrhS(8, maxS=2, uslov=U, key='pt')
        print(f"  {nm:44} {ll('pt', F):.4f} | {ll('ft', S8):.4f} | sajt-pravilo top4 {rep(t4)[:13]} top8 {rep(t8)[:13]} | PREKO P/A top1 {rep(vrhO(1, lambda x: 1 - x['pt'] >= .55, key='pt'), 'o')[:13]} top2 {rep(vrhO(2, lambda x: 1 - x['pt'] >= .55, key='pt'), 'o')[:13]}")
    E = BASE + ['mt', 'hot', 'tempo', 'minsd']
    proba('osnovni (bez novih)', BASE, lambda x: None)
    proba('novi, linearno (mt ±8, minsd 0–10)', E, lambda x: x['X'].update(mt=clip(x['mintrend'], -8, 8), minsd=clip(x['minsd'], 0, 10)))
    proba('mt samo pad (−8..+1), minsd do 4,5', E, lambda x: x['X'].update(mt=clip(x['mintrend'], -8, 1), minsd=clip(x['minsd'], 0, 4.5)))
    proba('mt samo pad (−8..0), minsd do 4,5', E, lambda x: x['X'].update(mt=clip(x['mintrend'], -8, 0), minsd=clip(x['minsd'], 0, 4.5)))
    proba('mt ±4, minsd do 4,5', E, lambda x: x['X'].update(mt=clip(x['mintrend'], -4, 4), minsd=clip(x['minsd'], 0, 4.5)))
    proba('samo mt pad + tempo', BASE + ['mt', 'tempo'], lambda x: x['X'].update(mt=clip(x['mintrend'], -8, 1)))
    proba('samo mt pad + hot + tempo', BASE + ['mt', 'hot', 'tempo'], lambda x: x['X'].update(mt=clip(x['mintrend'], -8, 1)))
if '--skokovi' in sys.argv:
    print('\n=== sajt-pravilo: skokovi ispod 0 / 1 / bez ograničenja ===')
    for k in [k for k in kola if k >= 8]:
        T_ = uci([x for x in F if x['kolo'] < k], BASE + ['mt', 'hot', 'tempo', 'minsd'])
        for x in FA:
            if x['kolo'] == k: x['f3'] = pr(T_, x)
    for ms in (0, 1, 4):
        t = vrhS(4, maxS=ms, uslov=U); t8 = vrhS(4, maxS=ms, uslov=lambda x: U(x) and x['kolo'] >= 8, key='f3')
        print(f"  skokova najviše {ms}: bez tog kola {rep(t)} | {dani(t)} | druga polovina {rep([x for x in t if x['kolo'] in H2])[:13]} | strogo unapred 8+ {rep(t8)}")
    S_ = [x for x in F if x['s'] == 'S' and x['u'] >= 1.6 and U(x)]
    for b0, b1 in ((.55, .62), (.62, .68), (.68, 1)):
        for nm, hh in (('prva pol.', H1), ('druga pol.', H2)):
            q = [x for x in S_ if b0 <= x['p3'] < b1 and x['kolo'] in hh]; print(f"    skokovi ispod p3 {b0}-{b1} {nm}: n{len(q):3} {sum(x['y'] for x in q) / max(1, len(q)):.1%}", end=' |')
        print()
