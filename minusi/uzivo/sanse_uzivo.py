"""Šanse živih tiketa: za svaki tiket bez promašaja (ili sa jednim, --jedan) koje parove čekamo, stanje i verovatnoću.
Par u toku: preostala produkcija ~ učinak po minutu (sezona) × očekivani preostali minuti igrača, raspodela Poisson sa
uvećanom varijansom. Par koji nije počeo: verovatnoća spoja iz izbora (sel). Tiket = proizvod (parovi nezavisni)."""
import json, sys, math, os, re, argparse, collections, unicodedata
sys.path.insert(0, os.path.dirname(__file__))
ap = argparse.ArgumentParser()
ap.add_argument('--planovi', nargs='+', required=True); ap.add_argument('--sel', nargs='+', required=True)
ap.add_argument('--utakmice', nargs='+', type=int, required=True); ap.add_argument('--dir', default='/tmp/live12')
ap.add_argument('--jedan', action='store_true'); ap.add_argument('--gotove', nargs='*', type=int, default=[])
a = ap.parse_args()
sys.argv = [sys.argv[0], '--planovi', *a.planovi, '--utakmice', *map(str, a.utakmice), '--dir', a.dir] + (['--gotove', *map(str, a.gotove)] if a.gotove else [])
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    import status_dan as SD
R = json.load(open('/home/claude/Euroleague/baza/rows.json'))
by = collections.defaultdict(list)
for r in R:
    if r['min'] > 0: by[SD.nk(r['k'])].append(r)
PR = {}
for f in a.sel:
    for x in json.load(open(f)): PR[(x['p'], x['s'], x['l'])] = x['pr']
def elapsed(g):
    d = json.load(open(os.path.join(a.dir, f'bs_{g}.json')))
    m = [sum(SD.minute(p['Minutes']) for p in s['PlayersStats']) for s in d['Stats']]
    return min(m) / 5 if m else 0
EL = {g: elapsed(g) for g in SD.GAME}
def pois_cdf(k, lam, disp=1.35):
    if k < 0: return 0.0
    # negativna binomna sa var = disp*lam
    if lam <= 0: return 1.0
    r = lam / (disp - 1); p = r / (r + lam)
    c = 0.0; pk = p ** r
    for i in range(int(k) + 1):
        c += pk; pk *= (i + r) / (i + 1) * (1 - p)
    return min(1.0, c)
def p_leg(l):
    st, v, b = SD.LS[(l['p'], l['s'], l['l'])]
    if st in ('prošla', 'vraćeno'): return 1.0, st, v, None
    if st == 'pala': return 0.0, st, v, None
    if st == 'čeka': return PR.get((l['p'], l['s'], l['l']), 0.55), st, None, None
    g = b['g']; el = EL[g]; ukupno = 40 if el < 40 else 45 if el < 45 else 50
    rem = max(0.0, ukupno - el)
    hist = by.get(SD.nk(l['p'])) or by.get({'daniel oturu': 'dan oturu'}.get(SD.nk(l['p']), '')) or []
    if hist:
        mins = sum(r['min'] for r in hist); rate = sum(r[l['s']] for r in hist) / mins; avgmin = mins / len(hist)
    else:
        rate = {'P': 0.45, 'S': 0.2, 'A': 0.1}[l['s']]; avgmin = 20
    exp_min = avgmin * rem / 40
    if b['min'] == 0 and el > 20: exp_min *= 0.3
    lam = rate * exp_min
    need = l['l'] - 0.5 - v
    return pois_cdf(math.floor(need), lam), st, v, (round(b['min']), round(rem, 1))
rows = []
for src in a.planovi:
    for i, t in enumerate(json.load(open(src))['tickets'], 1):
        legs = t['legs']; ps = [p_leg(l) for l in legs]
        miss = sum(1 for p in ps if p[1] == 'pala')
        if miss > (1 if a.jedan else 0): continue
        prob = math.prod(p[0] for p in ps if p[1] != 'pala')
        rows.append((prob, os.path.basename(src), i, t, ps, miss))
rows.sort(key=lambda r: -r[0])
for prob, src, i, t, ps, miss in rows:
    o = math.prod(l['u'] for l, p in zip(t['legs'], ps) if p[1] != 'vraćeno')
    n = sum(1 for p in ps if p[1] != 'vraćeno')
    bon = {7: .11, 8: .16, 9: .21, 10: .26, 11: .31, 12: .36, 13: .41, 14: .46}.get(n, 0)
    print(f"\n{('T1' if 'talas1' in src else 'T2')}-{i} ({len(t['legs'])} parova, {t['stake']} din, isplata ~{t['stake']*o*(1+bon):,.0f}) šansa {prob*100:.1f}%" + (' [jedan promašaj, igra za povraćaj]' if miss else ''))
    for l, p in zip(t['legs'], ps):
        if p[1] in ('prošla', 'vraćeno', 'pala'): continue
        info = f"sada {p[2]} ({p[3][0]} min, do kraja ~{p[3][1]} min)" if p[1] == 'ide' else 'nije počelo'
        print(f"   {l['p']} {l['s']} ispod {l['l']}: {info} → {p[0]*100:.0f}%")
print('\nukupno tiketa:', len(rows), '| očekivano dobitnih:', round(sum(r[0] for r in rows if r[5] == 0), 2))
