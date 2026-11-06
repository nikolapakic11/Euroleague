"""Analiza logike i procena (6.11.2026, Nikola: „napravi analizu logike i procena i vidi može li bolje“).

  python3 procene/provera/logika_2026-11-06.py

Na granicama iz provere (procene/provera/granice.json, walk-forward model), kola 6–10:
  1) sam model: pristrasnost očekivanja po stavci i nivou, kalibracija verovatnoće modela
  2) varijante spoja (svaka podešena samo na ranijim kolima): tržište, model, sadašnji spoj, bez Platt-a,
     bez vremenskih težina, fiksni udeo modela, spoj sa skupljanjem ka tržištu
  3) izbor: prednost ≥ prag, po strani i pojasevima; povraćaj na kvoti te kladionice
"""
import collections, json, math, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte')); os.chdir(KOREN)
import spajanje as S

R = json.load(open('procene/provera/granice.json'))
R = [r for r in R if r.get('preko') is not None and r['ishod'] != r['l']]
kola = sorted({r['kolo'] for r in R})
lg, sig = S.lg, lambda z: 1 / (1 + math.exp(-z))


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


print('Granica sa ishodom:', len(R), dict(collections.Counter(r['kolo'] for r in R)))

# ---------- 1) model sam ----------
print('\n1) MODEL SAM')
for s in 'PSA':
    X = [r for r in R if r['s'] == s]
    print(f"  {s}: očekivano {st.mean(r['mu'] for r in X):.2f}, stvarno {st.mean(r['ishod'] for r in X):.2f}, granica {st.mean(r['l'] for r in X):.2f}"
          f" | preko: model {st.mean(r['pm'] for r in X):.3f}, tržište {st.mean(r['tr'] for r in X):.3f}, stvarno {st.mean(r['preko'] for r in X):.3f}")
print('  model − tržište (razlika verovatnoće za preko) i šta se desilo:')
for lo, hi in ((-1, -.15), (-.15, -.07), (-.07, -.02), (-.02, .02), (.02, .07), (.07, .15), (.15, 1)):
    X = [r for r in R if lo <= r['pm'] - r['tr'] < hi]
    if X:
        print(f"   {lo:+.2f}..{hi:+.2f}: n={len(X):4} model {st.mean(r['pm'] for r in X):.3f} tržište {st.mean(r['tr'] for r in X):.3f} stvarno {st.mean(r['preko'] for r in X):.3f}")
print('  očekivanje modela vs granica (mu − l) i stvarno preko:')
for lo, hi in ((-9, -3), (-3, -1.5), (-1.5, -.5), (-.5, .5), (.5, 1.5), (1.5, 3), (3, 9)):
    X = [r for r in R if lo <= r['mu'] - r['l'] < hi]
    if X:
        print(f"   {lo:+}..{hi:+}: n={len(X):4} model {st.mean(r['pm'] for r in X):.3f} tržište {st.mean(r['tr'] for r in X):.3f} stvarno {st.mean(r['preko'] for r in X):.3f}")


# ---------- 2) varijante ----------
def fiksni(a, R0):
    """logit p = c + a·logit pm + (1−a)·logit tr; c tako da se prosek slaže sa poslednja 2 kola."""
    km = max(r['kolo'] for r in R0)
    Y = [r for r in R0 if r['kolo'] > km - 2]
    c = 0.0
    for _ in range(20):
        m = st.mean(sig(c + a * lg(r['pm']) + (1 - a) * lg(r['tr'])) for r in Y)
        c += (lg(st.mean(r['preko'] for r in Y)) - lg(m)) * 0.8
    return lambda r: sig(c + a * lg(r['pm']) + (1 - a) * lg(r['tr']))


def sadasnji(R0, platt=True, vreme=True):
    w = S.podesi_vreme(R0) if vreme else S.podesi(R0)
    km = max(r['kolo'] for r in R0)
    kal = None
    if platt:
        sk = [dict(s=r['s'], p=S.preko(w, r['s'], r['pm'], r['tr']), y=r['preko']) for r in R0 if r['kolo'] > km - 3]
        kal = {s: S.platt([x for x in sk if x['s'] == s]) for s in 'PSA'}
    return lambda r: S.preko_kal(w, kal, r['s'], r['pm'], r['tr'])


def skupljen(R0, k):
    """sadašnji spoj, pa odstupanje od tržišta skupljeno faktorom k (logit)."""
    f = sadasnji(R0)
    return lambda r: sig(lg(r['tr']) + k * (lg(f(r)) - lg(r['tr'])))


VAR = {
    'tržište (fer kvota)': lambda R0: (lambda r: r['tr']),
    'model sam': lambda R0: (lambda r: r['pm']),
    'SADAŠNJI spoj (vreme + Platt)': lambda R0: sadasnji(R0),
    'spoj bez Platt-a': lambda R0: sadasnji(R0, platt=False),
    'spoj bez vremenskih težina': lambda R0: sadasnji(R0, vreme=False),
    'fiksno 20% model': lambda R0: fiksni(0.2, R0),
    'fiksno 30% model': lambda R0: fiksni(0.3, R0),
    'fiksno 40% model': lambda R0: fiksni(0.4, R0),
    'sadašnji, odstupanje × 0,5': lambda R0: skupljen(R0, 0.5),
    'sadašnji, odstupanje × 0,7': lambda R0: skupljen(R0, 0.7),
}
P = collections.defaultdict(dict)   # varijanta -> id reda -> p
for k in kola:
    R0 = [r for r in R if r['kolo'] < k]
    if len(R0) < 400:
        continue
    for ime, fn in VAR.items():
        f = fn(R0)
        for i, r in enumerate(R):
            if r['kolo'] == k:
                P[ime][i] = f(r)
ids = sorted(P['tržište (fer kvota)'])
print(f'\n2) VARIJANTE (walk-forward, kola {sorted({R[i]["kolo"] for i in ids})}, n={len(ids)}) — manji log gubitak je bolji')
baza = st.mean(ll(P['tržište (fer kvota)'][i], R[i]['preko']) for i in ids)
for ime in VAR:
    v = st.mean(ll(P[ime][i], R[i]['preko']) for i in ids)
    po_k = {k: st.mean(ll(P[ime][i], R[i]['preko']) - ll(P['tržište (fer kvota)'][i], R[i]['preko']) for i in ids if R[i]['kolo'] == k) for k in sorted({R[i]['kolo'] for i in ids})}
    print(f"  {ime:32} {v:.4f} ({v - baza:+.4f} vs tržište) po kolima: " + ' '.join(f'{k}:{d * 1000:+.1f}' for k, d in po_k.items()))


# ---------- 3) izbor ----------
def stavke(ime, prag=0.04, pp_min=0.54, strana=None):
    """najbolja kvota po (igrač, dan, stavka, granica, strana) među kladionicama; prednost na fer te kladionice."""
    najb = {}
    for i in ids:
        r = R[i]; p = P[ime][i]
        for sd, pp, kv, fer, ok in (('o', p, r['o'], r['tr'], r['preko'] == 1), ('u', 1 - p, r['u'], 1 - r['tr'], r['preko'] == 0)):
            if kv < S.KVOTA_MIN or pp < pp_min or pp - fer < prag or (strana and sd != strana):
                continue
            key = (r['k'], r['dan'], r['s'], sd)
            if key not in najb or pp - fer > najb[key]['ed']:
                najb[key] = dict(ed=pp - fer, pp=pp, kv=kv, ok=ok, sd=sd, fer=fer, kolo=r['kolo'])
    return list(najb.values())


def z(X):
    if not X:
        return '—'
    n = len(X); pr = sum(x['ok'] for x in X); d = sum((x['kv'] - 1) if x['ok'] else -1 for x in X)
    return f"{pr}/{n} {pr / n:.0%} povr. {d / n:+.1%}"


print('\n3) IZBOR (prednost ≥ prag, verovatnoća ≥ 54%, najbolja prednost po igrač-stavka-strana)')
for ime in ('SADAŠNJI spoj (vreme + Platt)', 'spoj bez Platt-a', 'fiksno 30% model', 'sadašnji, odstupanje × 0,7', 'sadašnji, odstupanje × 0,5'):
    for prag in (0.04, 0.06, 0.08):
        X = stavke(ime, prag)
        print(f"  {ime:32} prednost ≥{prag:.0%}: {z(X):24} | PLUS {z([x for x in X if x['sd'] == 'o']):22} | MINUS {z([x for x in X if x['sd'] == 'u'])}")
print('\n  sadašnji spoj, prednost ≥4%, po pojasu verovatnoće:')
X = stavke('SADAŠNJI spoj (vreme + Platt)', 0.04)
for lo, hi in ((0.54, 0.56), (0.56, 0.60), (0.60, 0.65), (0.65, 1)):
    Y = [x for x in X if lo <= x['pp'] < hi]
    print(f"   {lo:.0%}–{hi:.0%}: {z(Y)} | PLUS {z([x for x in Y if x['sd'] == 'o'])} | MINUS {z([x for x in Y if x['sd'] == 'u'])}")
print('  po prednosti:')
for lo, hi in ((0.04, 0.06), (0.06, 0.08), (0.08, 0.12), (0.12, 1)):
    Y = [x for x in X if lo <= x['ed'] < hi]
    print(f"   {lo:.0%}–{hi:.0%}: {z(Y)} | PLUS {z([x for x in Y if x['sd'] == 'o'])} | MINUS {z([x for x in Y if x['sd'] == 'u'])}")
print('  po kolu:', {k: z([x for x in X if x['kolo'] == k]) for k in sorted({x['kolo'] for x in X})})
print('\n  kalibracija sadašnjeg spoja (izabrana strana):')
for lo, hi in ((0.5, 0.54), (0.54, 0.58), (0.58, 0.62), (0.62, 0.7), (0.7, 1)):
    Y = [(max(P['SADAŠNJI spoj (vreme + Platt)'][i], 1 - P['SADAŠNJI spoj (vreme + Platt)'][i]),
          (P['SADAŠNJI spoj (vreme + Platt)'][i] >= 0.5) == (R[i]['preko'] == 1), R[i]) for i in ids]
    Y = [y for y in Y if lo <= y[0] < hi]
    if Y:
        fer = st.mean(r['tr'] if p >= 0.5 else 1 - r['tr'] for p, r in ((P['SADAŠNJI spoj (vreme + Platt)'][i], R[i]) for i in ids) if lo <= max(p, 1 - p) < hi)
        print(f"   {lo:.0%}–{hi:.0%}: n={len(Y):4} predviđeno {st.mean(y[0] for y in Y):.3f} stvarno {st.mean(y[1] for y in Y):.3f} tržište {fer:.3f}")

# ---------- 4) stabilnost predloga izmene ----------
print('\n4) STABILNOST: varijante po kolu i broj po danu (prednost na fer te kladionice)')
broj_dana = len({R[i]['dan'] for i in ids})
for ime, prag in (('SADAŠNJI spoj (vreme + Platt)', 0.04), ('sadašnji, odstupanje × 0,5', 0.04), ('sadašnji, odstupanje × 0,5', 0.05),
                  ('sadašnji, odstupanje × 0,5', 0.06), ('sadašnji, odstupanje × 0,7', 0.06), ('fiksno 30% model', 0.06)):
    X = stavke(ime, prag, pp_min=0.53)
    print(f"  {ime:30} ≥{prag:.0%}: {z(X):24} {len(X) / broj_dana:4.1f}/dan | po kolu: " + ', '.join(f"{k}: {z([x for x in X if x['kolo'] == k])}" for k in sorted({x['kolo'] for x in X})))
print('\n  kalibracija posle skupljanja × 0,5 (izabrana strana):')
for lo, hi in ((0.5, 0.53), (0.53, 0.56), (0.56, 0.6), (0.6, 1)):
    Y = [(max(p, 1 - p), (p >= 0.5) == (R[i]['preko'] == 1)) for i in ids for p in [P['sadašnji, odstupanje × 0,5'][i]] if lo <= max(p, 1 - p) < hi]
    if Y:
        print(f"   {lo:.0%}–{hi:.0%}: n={len(Y):4} predviđeno {st.mean(y[0] for y in Y):.3f} stvarno {st.mean(y[1] for y in Y):.3f}")
