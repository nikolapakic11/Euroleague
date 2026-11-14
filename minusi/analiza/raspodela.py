"""Kako bi prošli odigrani dani da su isti parovi bili ravnomernije raspoređeni po tiketima.

Za svaki dan uzima odigrane tikete (stanje aplikacije) i njihove stvarne ishode. Skup parova,
broj tiketa, broj parova po tiketu i ulozi ostaju isti; menja se samo koliko puta se koji par
pojavljuje (izloženost):
  stvarno        - tiketi kako su odigrani
  a=1.0          - ista izloženost kao stvarno, ali parovi nasumično upareni (kontrola)
  a=0.5          - izloženost ublažena (koren stvarne)
  a=0.0          - potpuno ravnomerno (svaki par približno isti broj puta)
Za a < 1 tiketi se slažu nasumično mnogo puta (--n), pa se daje prosek i raspon.
Isplata: ulog * kvota * (1 + Admiral bonus), povraćaj kad padne tačno jedan par i ima bar 7
parova koji se računaju; povraćaj = prosečan povraćaj na 100 din iz dosadašnjih tiketa.
"""
import json, random, math, collections, argparse, statistics, sys, os

ap = argparse.ArgumentParser()
ap.add_argument('--n', type=int, default=300)
ap.add_argument('--od', default='2026-09-01')
ap.add_argument('--seed', type=int, default=7)
ap.add_argument('--izlaz', default=None)
a = ap.parse_args()
random.seed(a.seed)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(BASE, 'aplikacija', 'stanje.json')))
R = S['results']

def bon(n):
    T = {4: .03, 5: .05, 6: .07, 7: .11, 8: .16, 9: .21, 10: .26}
    return .26 + .05 * (n - 10) if n > 10 else T.get(n, 0)

def key(t, l):
    return '|'.join([str(t['round']).strip(), l['p'].strip().lower(), l['stat'], repr(l['line']) if isinstance(l['line'], float) else str(l['line'])])

def status(k, line):
    r = R.get(k)
    if not r: return 'pending'
    if r.get('dnp'): return 'void'
    if r.get('actual') is None: return r.get('outcome', 'pending')
    return 'hit' if r['actual'] < line else 'miss'

refs = [t['refund'] / t['stake'] for t in S['tickets'] if t.get('refund')]
REF = sum(refs) / len(refs)  # povraćaj po dinaru uloga (ukupni prosek)
_r8 = [t['refund'] / t['stake'] for t in S['tickets'] if t.get('refund') and len(t['legs']) <= 8]
_r9 = [t['refund'] / t['stake'] for t in S['tickets'] if t.get('refund') and len(t['legs']) >= 9]
REF8 = sum(_r8) / len(_r8); REF9 = sum(_r9) / len(_r9) if _r9 else 5.0
def refm(nv): return REF9 if nv >= 9 else REF8   # 9+ parova: do sada uvek 5x uloga

def isplata(legs, stake, info):
    """legs: lista ključeva; info[k] = (kvota, status, igrač)"""
    m = 0; o = 1; nv = 0
    for k in legs:
        q, st, _ = info[k]
        if st == 'pending': return None
        if st == 'void': continue
        nv += 1
        if st == 'miss': m += 1
        else: o *= q
    if m == 0: return stake * o * (1 + bon(nv)), 'dobitak', 0
    if m == 1 and nv >= 7: return stake * refm(nv), 'povraćaj', stake
    return 0.0, ('jedan' if m == 1 else 'pao'), 0

def slozi(sizes, info, target):
    """Pohlepno slaganje: na svaki tiket idu parovi sa najviše preostalih mesta (uz šum), bez
    istog igrača dvaput i bez ponovljenog tiketa."""
    for _ in range(50):
        rem = dict(target); out = []; seen = set(); ok = True
        order = sorted(range(len(sizes)), key=lambda i: -sizes[i])
        for i in order:
            n = sizes[i]
            for _try in range(30):
                cand = sorted(rem, key=lambda k: -(rem[k] + random.random() * 0.9))
                t = []; pl = set()
                for k in cand:
                    if rem[k] <= 0 and len(t) < n and any(rem[x] > 0 for x in cand if x not in t and info[x][2] not in pl):
                        continue
                    if info[k][2] in pl: continue
                    t.append(k); pl.add(info[k][2])
                    if len(t) == n: break
                fs = frozenset(t)
                if len(t) == n and fs not in seen: break
            else:
                ok = False; break
            seen.add(fs)
            for k in t: rem[k] -= 1
            out.append((i, t))
        if ok:
            out.sort(); return [t for _, t in out]
    return None

def cilj(counts, alpha, slots):
    w = {k: c ** alpha for k, c in counts.items()}
    s = sum(w.values()); raw = {k: w[k] / s * slots for k in w}
    base = {k: int(math.floor(v)) for k, v in raw.items()}
    left = slots - sum(base.values())
    for k in sorted(raw, key=lambda k: -(raw[k] - base[k]))[:left]: base[k] += 1
    return base

dani = collections.defaultdict(list)
for t in S['tickets']:
    if t['date'] >= a.od and len(t['legs']) >= 4: dani[t['date']].append(t)

ALPH = [1.0, 0.5, 0.0]
red = []; tot = collections.defaultdict(float); totn = collections.defaultdict(list)
tier = collections.defaultdict(lambda: [0, 0]); kv = collections.defaultdict(list)
for d in sorted(dani):
    T = dani[d]
    info = {}; counts = collections.Counter()
    for t in T:
        for l in t['legs']:
            k = key(t, l); info[k] = (l['odds'], status(k, l['line']), l['p'].strip().lower()); counts[k] += 1
    if any(v[1] == 'pending' for v in info.values()): continue
    # učinak parova po izloženosti (gornja trećina po broju tiketa naspram ostatka)
    ks = sorted(counts, key=lambda k: -counts[k]); n3 = max(1, len(ks) // 3)
    for j, k in enumerate(ks):
        st = info[k][1]
        if st == 'void': continue
        g = 'najviše' if j < n3 else ('srednje' if j < 2 * n3 else 'najmanje')
        tier[g][0] += st == 'hit'; tier[g][1] += 1; kv[g].append(info[k][0])
    sizes = [len(t['legs']) for t in T]; stakes = [t['stake'] for t in T]
    ulog = sum(stakes); slots = sum(sizes)
    act = [isplata([key(t, l) for l in t['legs']], t['stake'], info) for t in T]
    r_act = sum(x[0] for x in act)
    stv = sum((t.get('bonus') or 0) + 0 for t in T)
    row = dict(dan=d, tiketa=len(T), parova=len(counts), ulog=round(ulog), hit=sum(v[1] == 'hit' for v in info.values()),
               nv=sum(v[1] != 'void' for v in info.values()), maxizl=round(max(counts.values()) / len(T), 2),
               stvarno=round(r_act), dob_stv=sum(x[1] == 'dobitak' for x in act), pov_stv=sum(x[1] == 'povraćaj' for x in act))
    tot['ulog'] += ulog; tot['stvarno'] += r_act
    tot['stv_dob'] += sum(x[0] for x in act if x[1] == 'dobitak'); tot['stv_ps'] += sum(x[2] for x in act)
    for al in ALPH:
        tg = cilj(counts, al, slots)
        res = []; dob = []; pov = []; wd = []; ps = []
        for _ in range(a.n):
            P = slozi(sizes, info, tg)
            if P is None: continue
            # najveći ulozi idu na veće tikete kao u stvarnosti (redosled po veličini isti)
            ordT = sorted(range(len(T)), key=lambda i: -sizes[i]); ordP = sorted(range(len(P)), key=lambda i: -len(P[i]))
            x = [isplata(P[ordP[j]], stakes[ordT[j]], info) for j in range(len(T))]
            wd.append(sum(v[0] for v in x if v[1] == 'dobitak')); ps.append(sum(v[2] for v in x))
            res.append(sum(v[0] for v in x)); dob.append(sum(v[1] == 'dobitak' for v in x)); pov.append(sum(v[1] == 'povraćaj' for v in x))
        if not res: continue
        res.sort()
        row[f'a{al}'] = dict(prosek=round(statistics.mean(res)), medijana=round(res[len(res) // 2]), p10=round(res[len(res) // 10]),
                             p90=round(res[len(res) * 9 // 10]), u_plusu=round(sum(r > ulog for r in res) / len(res), 2),
                             bar_jedan=round(sum(x > 0 for x in dob) / len(dob), 2), dobitnih=round(statistics.mean(dob), 2),
                             povracaja=round(statistics.mean(pov), 2))
        tot[f'a{al}'] += statistics.mean(res); totn[f'a{al}'].append(res)
        tot[f'dob{al}'] += statistics.mean(wd); tot[f'ps{al}'] += statistics.mean(ps)
    red.append(row)

lines = []
P = lines.append
P(f"povraćaj računat kao {REF*100:.0f} din na 100 din uloga (prosek dosadašnjih povraćaja)")
P(f"{'dan':10s} {'tik':>3s} {'par':>3s} {'prolaz':>7s} {'maxizl':>6s} {'ulog':>6s} | {'stvarno':>7s} dob pov | {'ista izl.':>9s} | {'ublaženo':>9s} p>0 | {'ravnomerno':>10s} p>0 u+ | rav.dob/pov")
for r in red:
    a1, a5, a0 = r.get('a1.0', {}), r.get('a0.5', {}), r.get('a0.0', {})
    P(f"{r['dan']:10s} {r['tiketa']:3d} {r['parova']:3d} {r['hit']:3d}/{r['nv']:<3d} {r['maxizl']:6.2f} {r['ulog']:6d} | {r['stvarno']:7d} {r['dob_stv']:3d} {r['pov_stv']:3d} | {a1.get('prosek',0):9d} | {a5.get('prosek',0):9d} {a5.get('bar_jedan',0):.2f} | {a0.get('prosek',0):10d} {a0.get('bar_jedan',0):.2f} {a0.get('u_plusu',0):.2f} | {a0.get('dobitnih',0):.2f}/{a0.get('povracaja',0):.2f}")
P('')
P(f"UKUPNO ulog {tot['ulog']:.0f} | stvarno vraćeno {tot['stvarno']:.0f} ({tot['stvarno']/tot['ulog']*100:.0f}%) | ista izloženost nasumično {tot['a1.0']:.0f} ({tot['a1.0']/tot['ulog']*100:.0f}%) | ublaženo {tot['a0.5']:.0f} ({tot['a0.5']/tot['ulog']*100:.0f}%) | ravnomerno {tot['a0.0']:.0f} ({tot['a0.0']/tot['ulog']*100:.0f}%)")
P('RAZDVOJENO (dobici | ulog na tiketima sa povraćajem | ukupno ako je povraćaj 0, 1x ili %.2fx uloga):' % REF)
for nm, dk, pk in [('stvarno', 'stv_dob', 'stv_ps')] + [(f'a={al}', f'dob{al}', f'ps{al}') for al in ALPH]:
    w = tot[dk]; p = tot[pk]
    P(f"  {nm:8s} dobici {w:8.0f} | povraćajni ulog {p:6.0f} | ukupno {w/tot['ulog']*100:4.0f}% / {(w+p)/tot['ulog']*100:4.0f}% / {(w+p*REF)/tot['ulog']*100:4.0f}%")
P('prolaz parova po izloženosti (u okviru dana): ' + ', '.join(f"{g} {v[0]}/{v[1]} = {v[0]/v[1]*100:.0f}% (prosečna kvota {statistics.mean(kv[g]):.2f})" for g, v in tier.items()))
# raspon ukupnog ishoda za ravnomerno: zbir nasumičnih slaganja po danima
for al in ALPH:
    L = totn[f'a{al}']
    sims = [sum(random.choice(x) for x in L) for _ in range(5000)]; sims.sort()
    P(f"  a={al}: ukupno vraćeno p10 {sims[500]:.0f}, medijana {sims[2500]:.0f}, p90 {sims[4500]:.0f}")
txt = '\n'.join(lines); print(txt)
if a.izlaz:
    open(a.izlaz, 'w').write(txt + '\n'); json.dump(red, open(a.izlaz.replace('.txt', '.json'), 'w'), ensure_ascii=False, indent=1)
