"""Dopuna analize raspodele (14.11.2026): uz ravnomernu izloženost, da li pomaže
  (1) jezgro: najkraća trećina tiketa složena od najverovatnijih parova (hibrid od 12.11.),
  (2) drugačije dužine tiketa za isti budžet (sve sedmice, sve osmice, šestice, desetke po 50).
Isti odigrani parovi i stvarni ishodi kao u raspodela.py.
"""
import json, random, math, collections, statistics, os, re, unicodedata, sys
sys.argv = [sys.argv[0], '--n', '1']
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R0 = os.path.dirname(BASE)
import importlib.util
spec = importlib.util.spec_from_file_location('rd', os.path.join(BASE, 'analiza', 'raspodela.py'))
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    rd = importlib.util.module_from_spec(spec); spec.loader.exec_module(rd)
random.seed(11)
N = int(os.environ.get('N', 120))

# verovatnoća iz spoja (kao spoj/analiza/raspored.py); bez nje 1/kvota
F = json.load(open(R0 + '/spoj/analiza/F.json'))
lg = lambda p: math.log(min(max(p, .02), .98) / (1 - min(max(p, .02), .98))); sg = lambda z: 1 / (1 + math.exp(-z))
SUF = {'jr', 'sr', 'ii', 'iii', 'iv'}
def nk(x):
    t = unicodedata.normalize('NFD', str(x or '')); t = ''.join(c for c in t if unicodedata.category(c) != 'Mn').lower()
    t = re.sub(r"[.']", '', t); t = re.sub(r'-', ' ', t); t = re.sub(r'[^a-z ]', '', t); return ' '.join(w for w in t.split() if w not in SUF)
PR = {}
for x in F:
    if x['izvor'] == 'admiral':
        PR[(x['dan'], nk(x['k']), x['s'], x['l'])] = sg(lg(1 - x['tr']) + 0.15 * (lg(x['mpu']) - lg(1 - x['tr']) - 0.16) + 0.30 * (lg(1 - x['pm']) - lg(1 - x['tr'])))

def slozi_jezgro(sizes, info, target, prob, udeo=1/3):
    rem = dict(target); out = {}; pl_ok = lambda t, k: info[k][2] not in {info[x][2] for x in t}
    order = sorted(range(len(sizes)), key=lambda i: sizes[i])
    nj = int(len(order) * udeo)
    seen = set()
    for n, i in enumerate(order):
        for _ in range(30):
            if n < nj: key = lambda k: (-(rem[k] > 0), -prob[k] + random.random() * 0.02)
            else: key = lambda k: -(rem[k] + random.random() * 0.9)
            t = []
            for k in sorted(rem, key=key):
                if pl_ok(t, k): t.append(k)
                if len(t) == sizes[i]: break
            if frozenset(t) not in seen: break
        seen.add(frozenset(t))
        for k in t: rem[k] -= 1
        out[i] = t
    return [out[i] for i in range(len(sizes))]

def vrednuj(P, stakes, info, ref=None):
    s = 0
    for t, st in zip(P, stakes):
        v = rd.isplata(t, st, info)
        s += v[0] if (v[1] != 'povraćaj' or ref is None) else st * ref
    return s

tot = collections.defaultdict(float); dani = 0; perday = collections.defaultdict(list)
VAR = {
    'ravnomerno (nasumično)': None,
    'ravnomerno + jezgro 1/3': 'j',
    'sve osmice po 100': (8, 100),
    'sve sedmice po 100': (7, 100),
    'sve šestice po 100': (6, 100),
    'sve desetke po 50': (10, 50),
    'sve devetke po 50': (9, 50),
    'sve osmice po 50': (8, 50),
}
for d in sorted(rd.dani):
    T = rd.dani[d]
    info = {}; counts = collections.Counter(); prob = {}
    for t in T:
        for l in t['legs']:
            k = rd.key(t, l); info[k] = (l['odds'], rd.status(k, l['line']), l['p'].strip().lower()); counts[k] += 1
            p = PR.get((t['date'], nk(l['p']), l['stat'], l['line'])); prob[k] = p if p is not None else 1 / l['odds'] / 1.04
    if any(v[1] == 'pending' for v in info.values()) or len(T) < 5: continue
    sizes = [len(t['legs']) for t in T]; stakes = [t['stake'] for t in T]; ulog = sum(stakes)
    dani += 1; tot['ulog'] += ulog
    for nm, v in VAR.items():
        if v is None or v == 'j':
            sz, stk = sizes, stakes
        else:
            n = int(round(ulog / v[1])); sz = [v[0]] * n; stk = [v[1]] * n
            if v[0] > len({info[k][2] for k in info}): continue
        tg = rd.cilj(counts, 0.0, sum(sz))
        r = []
        for _ in range(N):
            P = slozi_jezgro(sz, info, tg, prob) if v == 'j' else rd.slozi(sz, info, tg)
            if P is None: continue
            if v is None or v == 'j':
                o1 = sorted(range(len(sz)), key=lambda i: -sz[i]); o2 = sorted(range(len(P)), key=lambda i: -len(P[i]))
                P2 = [None] * len(P)
                for a_, b_ in zip(o1, o2): P2[a_] = P[b_]
                P = P2
            r.append((vrednuj(P, stk, info), vrednuj(P, stk, info, 0.0), vrednuj(P, stk, info, 1.0)))
        if not r: continue
        for j, lab in enumerate(['', '_bezpov', '_pov1']):
            tot[nm + lab] += statistics.mean(x[j] for x in r)
        perday[nm].append(statistics.mean(x[0] for x in r) - ulog)

import random as _r
def _bs(a,b):
    d=[x-y for x,y in zip(perday[a],perday[b])]
    bs=sorted(sum(_r.choice(d) for _ in d) for _ in range(10000))
    return f"{a} - {b}: bolje {sum(x>0 for x in d)}/{len(d)} dana, razlika {sum(d):.0f}, 90% raspon {bs[500]:.0f}..{bs[9500]:.0f}, P(<0) {sum(v<0 for v in bs)/1e4:.3f}"
print(f"dana {dani}, ulog {tot['ulog']:.0f}; povraćaj: po dužini ({rd.REF8:.2f}x za 7-8 parova, {rd.REF9:.2f}x za 9+) / bez povraćaja / povraćaj = ulog")
for nm in VAR:
    if nm not in tot: continue
    pd = perday[nm]
    print(f"  {nm:26s} {tot[nm]/tot['ulog']*100:4.0f}% / {tot[nm+'_bezpov']/tot['ulog']*100:4.0f}% / {tot[nm+'_pov1']/tot['ulog']*100:4.0f}%  | dana u plusu (prosek slaganja) {sum(x>0 for x in pd)}/{len(pd)}")
print(_bs('ravnomerno + jezgro 1/3','ravnomerno (nasumično)'))
print(_bs('sve desetke po 50','sve osmice po 100'))
print(_bs('sve osmice po 100','sve šestice po 100'))
print(_bs('sve osmice po 100','sve sedmice po 100'))
