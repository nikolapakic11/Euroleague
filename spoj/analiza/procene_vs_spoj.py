"""Provera 19.11.2026: (1) jaki minusi samog modela procena naspram spoja, (2) filter izostanaka: novi naspram starih izostanaka.
  python3 spoj/analiza/procene_vs_spoj.py
Koristi an3.py (F.json, p3 = spoj bez tog kola, f3 = spoj učen samo na ranijim kolima)."""
import io, os, sys, contextlib, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(R, 'spoj/analiza/an3.py'), encoding='utf8').read()
src = src[:src.index("print('  po stavci (p3")]
g = {'__file__': os.path.join(R, 'spoj/analiza/an3.py'), '__name__': 'an3_deo'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, 'an3', 'exec'), g)
F, FA, vrhN, rep, kola, byteam, rows = g['F'], g['FA'], g['vrhN'], g['rep'], g['kola'], g['byteam'], g['rows']

M = [('spoj p3 (bez tog kola)', lambda x: x['p3']), ('procene sam (1−pm)', lambda x: 1 - x['pm']),
     ('procene prednost (tr−pm)', lambda x: x['tr'] - x['pm']), ('tržište (1−tr)', lambda x: 1 - x['tr'])]
print('=== 1. Minusi po danu (Admiral, jedan po igraču, najviše 2 po utakmici, kvota ≥1,60) ===')
for naziv, skup in (('sva kola', F), ('kola 8+', [x for x in F if x['kolo'] >= 8]), ('kola 10+', [x for x in F if x['kolo'] >= 10])):
    print(f'-- {naziv} (n={len(skup)}, dana {len({x["dan"] for x in skup})}) --')
    for nm, sc in M + ([('spoj f3 (samo ranija kola)', lambda x: x['f3'])] if naziv != 'sva kola' else []):
        print(f"  {nm:28} top4 {rep(vrhN(sc, 4, skup=skup))} | top8 {rep(vrhN(sc, 8, skup=skup))} | top15 {rep(vrhN(sc, 15, po_ut=4, skup=skup))}")
print('\n  pragovi (svi parovi iznad praga, kvota ≥1,60):')
for nm, sc in M[:2]:
    for t in (.55, .58, .60, .65):
        S = [x for x in F if x['u'] >= 1.6 and sc(x) >= t]
        print(f"    {nm:24} ≥{t:.2f}: {rep(S)}")
print('\n  slaganje: oba jaka (p3≥0,55 i 1−pm≥0,55) / samo spoj / samo procene, kvota ≥1,60:')
for nm, u in (('oba', lambda x: x['p3'] >= .55 and 1 - x['pm'] >= .55), ('samo spoj', lambda x: x['p3'] >= .55 and 1 - x['pm'] < .55),
              ('samo procene', lambda x: x['p3'] < .55 and 1 - x['pm'] >= .55)):
    print(f"    {nm:14} {rep([x for x in F if x['u'] >= 1.6 and u(x)])}")

print('\n=== 2. Izostanci: novi (igrač propustio 0–2 utakmice pre ove) naspram starih (3+) ===')
# stvarni izostanci tog dana: igrač rotacije (bar 3 utakmice, prosek ≥10 min pre dana) koji tog dana nije igrao
tim_dani = {t: sorted(D) for t, D in byteam.items()}
cache = {}
def izost(team, dan):
    if (team, dan) in cache: return cache[(team, dan)]
    pre = collections.defaultdict(list)
    for d in tim_dani[team]:
        if d < dan:
            for r in byteam[team][d]:
                if r['min'] > 0: pre[r['k']].append(r['min'])
    rot = {k: sum(m) / len(m) for k, m in pre.items() if len(m) >= 3 and sum(m) / len(m) >= 10}
    danas = {r['k'] for r in byteam[team].get(dan, []) if r['min'] > 0}
    novi = stari = 0.0
    for k, m in rot.items():
        if k in danas: continue
        prop = 0
        for d in reversed([d for d in tim_dani[team] if d < dan]):
            if any(r['k'] == k and r['min'] > 0 for r in byteam[team][d]): break
            prop += 1
        if prop >= 3: stari += m
        else: novi += m
    cache[(team, dan)] = (novi, stari); return novi, stari
for x in F:
    x['iz_novi'], x['iz_stari'] = izost(x['team'], x['dan'])
def red(S, nm):
    if not S: print(f'    {nm:46} n=0'); return
    n = len(S); y = sum(x['y'] for x in S) / n; mk = sum(1 - x['tr'] for x in S) / n; sp = sum(x['p3'] for x in S) / n
    print(f"    {nm:46} n={n:4} ispod {y:5.1%} | tržište {mk:5.1%} | spoj {sp:5.1%} | razlika od tržišta {y - mk:+.1%}")
for s_nm, us in (('sve stavke', lambda x: True), ('poeni', lambda x: x['s'] == 'P'), ('skokovi i asistencije', lambda x: x['s'] in 'SA')):
    print(f'  -- {s_nm} --')
    B = [x for x in F if us(x)]
    red([x for x in B if x['iz_novi'] + x['iz_stari'] < 20], 'tim bez većih izostanaka (<20 min)')
    red([x for x in B if x['iz_novi'] >= 35], 'novi izostanci ≥35 min')
    red([x for x in B if x['iz_novi'] < 20 and x['iz_stari'] >= 35], 'samo stari izostanci ≥35 min (novi <20)')
    red([x for x in B if x['iz_novi'] + x['iz_stari'] >= 35], 'ukupno ≥35 (kao filter)')
print('\n  jaki po spoju (p3 ≥0,55, kvota ≥1,60) u timovima sa izostancima:')
J = [x for x in F if x['p3'] >= .55 and x['u'] >= 1.6]
red([x for x in J if x['iz_novi'] >= 35], 'novi ≥35')
red([x for x in J if x['iz_novi'] < 20 and x['iz_stari'] >= 35], 'samo stari ≥35')
red([x for x in J if x['iz_novi'] + x['iz_stari'] < 20], 'bez izostanaka')

print('\n=== 3. Mešavine za rangiranje (minusi po danu) ===')
MX = [('spoj p3', lambda x: x['p3']), ('procene sam', lambda x: 1 - x['pm']),
      ('prosek p3 i procena', lambda x: (x['p3'] + 1 - x['pm']) / 2), ('manji od dva (oba moraju)', lambda x: min(x['p3'], 1 - x['pm'])),
      ('p3, uslov procene ≥0,55', lambda x: x['p3'] if 1 - x['pm'] >= .55 else 0)]
for naziv, skup in (('sva kola', F), ('kola 8+', [x for x in F if x['kolo'] >= 8]), ('kola 10+', [x for x in F if x['kolo'] >= 10])):
    print(f'-- {naziv} --')
    for nm, sc in MX:
        print(f"  {nm:28} top4 {rep(vrhN(sc, 4, skup=skup))} | top8 {rep(vrhN(sc, 8, skup=skup))} | top15 {rep(vrhN(sc, 15, po_ut=4, skup=skup))}")

print('\n=== 4. Prosek (p3 + procene)/2: pragovi, kvota ≥1,60 ===')
for naziv, skup in (('sva kola', F), ('kola 10+', [x for x in F if x['kolo'] >= 10])):
    for t in (.55, .58, .60, .62, .65):
        S = [x for x in skup if x['u'] >= 1.6 and (x['p3'] + 1 - x['pm']) / 2 >= t]
        print(f"  {naziv:9} ≥{t:.2f}: {rep(S)} | po danu {len(S) / len({x['dan'] for x in skup}):.1f}")
