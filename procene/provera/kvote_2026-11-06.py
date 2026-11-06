"""Kvote i izbor predloga (6.11.2026, Nikola: ne sme sve da budu najniže kvote, treba raznovrsnosti i kvota 1,8–1,9).

  python3 procene/provera/kvote_2026-11-06.py

Walk-forward kola 5–10 (spajanje podesi_vreme i kalibracija iz ranijih kola). 1) Tačnost po visini kvote:
predviđeno, stvarno, povraćaj za izabranu stranu. 2) Pravila izbora dana na širem bazenu (sve glavne granice,
jedan predlog po igraču, forma, najviše 4 iz utakmice i 2 iz tima, najmanje 4, najviše 12):
  - po verovatnoći (sada), - po prednosti nad tržištem (verovatnoća − fer verovatnoća kvote),
  - po očekivanoj zaradi (EV), - po verovatnoći uz ograničen broj niskih kvota.
"""
import collections, json, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte')); os.chdir(KOREN)
import spajanje as S, predlozi as PR
from model import Baza
B = Baza(); info = {(x['k'], x['dan']): x for x in B.rows}
R = [r for r in json.load(open('procene/provera/granice.json')) if (r['k'], r['dan']) in info]
kola = sorted({r['kolo'] for r in R})

K = []          # kandidat = jedna strana jedne glavne granice
for k in kola:
    ranije = [r for r in R if r['kolo'] < k]
    if len(ranije) < 250:
        continue
    w = S.podesi_vreme(ranije)
    kmax = max(r['kolo'] for r in ranije)
    sk = [dict(s=r['s'], p=S.preko(w, r['s'], r['pm'], r['tr']), y=r['preko']) for r in ranije if r['kolo'] > kmax - 3]
    kal = {s: S.platt([x for x in sk if x['s'] == s]) for s in 'PSA'}
    for r in R:
        if r['kolo'] != k:
            continue
        x = info[(r['k'], r['dan'])]
        po = S.kalibrisi(S.preko(w, r['s'], r['pm'], r['tr']), kal, r['s'])
        for strana, pp, kv, fer, ok in (('o', po, r['o'], r['tr'], r['preko'] == 1), ('u', 1 - po, r['u'], 1 - r['tr'], r['preko'] == 0)):
            K.append(dict(k=r['k'], igr=r['k'], tim=x['team'], g=x['g'], dan=r['dan'], s=r['s'], strana=strana, l=r['l'],
                          pp=pp, kvota=kv, fer=fer, ev=pp * kv - 1, pred=pp - fer, prosao=ok, kolo=k))


def z(X):
    if not X:
        return '—'
    n = len(X); pr = sum(x['prosao'] for x in X); d = sum((x['kvota'] - 1) if x['prosao'] else -1 for x in X)
    return f"{pr}/{n} {pr / n:.1%} {d / n:+.1%} (kvota {st.mean(x['kvota'] for x in X):.2f})"


KOR = [(1.0, 1.60), (1.60, 1.75), (1.75, 1.90), (1.90, 9)]
print('1) Strana koju spoj vidi sa bar 58%, po kvoti:')
for lo, hi in KOR:
    X = [c for c in K if c['pp'] >= 0.58 and lo <= c['kvota'] < hi]
    if X:
        print(f"   kvota {lo:.2f}–{hi:.2f}: predviđeno {st.mean(c['pp'] for c in X):.3f} | {z(X)}")
print('   prednost nad tržištem ≥ 4 poena, po kvoti:')
for lo, hi in KOR:
    X = [c for c in K if c['pred'] >= 0.04 and lo <= c['kvota'] < hi]
    if X:
        print(f"   kvota {lo:.2f}–{hi:.2f}: predviđeno {st.mean(c['pp'] for c in X):.3f} fer {st.mean(c['fer'] for c in X):.3f} | {z(X)}")

po_dan = collections.defaultdict(list)
for c in K:
    if c['kvota'] >= S.KVOTA_MIN:
        po_dan[c['dan']].append(c)


def dan(P, ocena, uslov, najm=4, najv=12, niske_max=None, niska=1.65):
    P = sorted([p for p in P], key=lambda p: -ocena(p))
    izab, igr = [], set()
    for p in P:
        if len(izab) >= najv:
            break
        if p['k'] in igr or sum(q['g'] == p['g'] for q in izab) >= 4 or sum(q['tim'] == p['tim'] for q in izab) >= 2:
            continue
        if niske_max is not None and p['kvota'] < niska and sum(q['kvota'] < niska for q in izab) >= niske_max:
            continue
        if not (uslov(p) or len(izab) < najm):
            continue
        f = PR.forma(B, p)
        if f[1] >= 4 and f[0] / f[1] < PR.DAN_FORMA_MIN:
            continue
        izab.append(p); igr.add(p['k'])
    return izab


VAR = {
    'verovatnoća ≥58% (sada)': (lambda p: p['pp'], lambda p: p['pp'] >= 0.58, {}),
    'verovatnoća ≥58%, najviše 3 ispod 1,65': (lambda p: p['pp'], lambda p: p['pp'] >= 0.58, dict(niske_max=3)),
    'verovatnoća ≥56%, najviše 3 ispod 1,65': (lambda p: p['pp'], lambda p: p['pp'] >= 0.56, dict(niske_max=3)),
    'prednost ≥4 p., verov. ≥54%': (lambda p: p['pred'], lambda p: p['pred'] >= 0.04 and p['pp'] >= 0.54, {}),
    'prednost ≥6 p., verov. ≥54%': (lambda p: p['pred'], lambda p: p['pred'] >= 0.06 and p['pp'] >= 0.54, {}),
    'EV ≥5%, verov. ≥54%': (lambda p: p['ev'], lambda p: p['ev'] >= 0.05 and p['pp'] >= 0.54, {}),
    'EV ≥8%, verov. ≥54%': (lambda p: p['ev'], lambda p: p['ev'] >= 0.08 and p['pp'] >= 0.54, {}),
    'EV ≥5%, verov. ≥56%, najviše 3 ispod 1,65': (lambda p: p['ev'], lambda p: p['ev'] >= 0.05 and p['pp'] >= 0.56, dict(niske_max=3)),
}
print('\n2) Izbor dana (12 dana):')
for ime, (oc, us, kw) in VAR.items():
    P = []
    for d, C in po_dan.items():
        P += dan(C, oc, us, **kw)
    pl = [p for p in P if p['strana'] == 'o']; mi = [p for p in P if p['strana'] == 'u']
    niske = [p for p in P if p['kvota'] < 1.65]; visoke = [p for p in P if p['kvota'] >= 1.75]
    print(f"   {ime:44} {len(P) / len(po_dan):4.1f}/dan | {z(P)} | PLUS {z(pl)} | MINUS {z(mi)} | ispod 1,65: {len(niske)}, od 1,75: {len(visoke)}")

print('\n3) Prednost ≥4 p. i verov. ≥54%, uz poželjan PLUS (do N najboljih PLUS po prednosti):')
for n_plus, pl_pp, pl_pred in ((2, 0.54, 0.02), (2, 0.52, 0.0), (2, 0.56, 0.0), (1, 0.54, 0.02)):
    P = []
    for d, C in po_dan.items():
        izab = dan(C, lambda p: p['pred'], lambda p: p['pred'] >= 0.04 and p['pp'] >= 0.54)
        L = sorted([c for c in C if c['strana'] == 'o' and c['pp'] >= pl_pp and c['pred'] >= pl_pred], key=lambda c: -c['pred'])
        for c in L:
            if sum(q['strana'] == 'o' for q in izab) >= n_plus:
                break
            if c['k'] in {q['k'] for q in izab} or sum(q['g'] == c['g'] for q in izab) >= 4 or sum(q['tim'] == c['tim'] for q in izab) >= 2:
                continue
            izab.append(c)
        P += izab
    pl = [p for p in P if p['strana'] == 'o']; mi = [p for p in P if p['strana'] == 'u']
    print(f"   PLUS do {n_plus}, verov. ≥{pl_pp:.0%}, prednost ≥{pl_pred:.0%}: {z(P)} | PLUS {z(pl)} | MINUS {z(mi)}")
P = []
for d, C in po_dan.items():
    P += dan(C, lambda p: p['pred'], lambda p: p['pred'] >= 0.04 and p['pp'] >= 0.54)
print('\n4) Po kolima (prednost ≥4 p., verov. ≥54%):', {k: z([p for p in P if p['kolo'] == k]) for k in kola if any(p['kolo'] == k for p in P)})
print('   po stavci:', {s: z([p for p in P if p['s'] == s]) for s in 'PSA'})
