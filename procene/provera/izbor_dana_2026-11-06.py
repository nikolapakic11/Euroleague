"""Izbor predloga za dan (odluka 6.11.2026): najmanje 4, a dalje koliko ih je dobrih; PLUS nije obavezan.

  python3 procene/provera/izbor_dana_2026-11-06.py

Walk-forward kola 5–10: spajanje (podesi_vreme) i kalibracija samo iz ranijih kola. Bazen po utakmici iz
izbor_utakmice bez obaveznog PLUS-a i bez dopune (PLUS_MIN=0, MIN_UT=0), pa za dan: svi sa kalibrisanom
verovatnoćom ≥ prag, uz formu i raznovrsnost (najviše 4 iz utakmice, 2 iz tima), najmanje 4, najviše 12.
Poredi se sa sadašnjim pravilom (bar 2 PLUS po utakmici, 6 po utakmici, 8 za dan, bar 3 PLUS).
"""
import collections, json, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte')); os.chdir(KOREN)
import spajanje as S, predlozi as PR
from model import Baza
B = Baza(); info = {(x['k'], x['dan']): x for x in B.rows}
R = [r for r in json.load(open('procene/provera/granice.json')) if (r['k'], r['dan']) in info]
kola = sorted({r['kolo'] for r in R})


def pools(plus_min, min_ut):
    out = collections.defaultdict(list)       # dan -> kandidati sa kal
    for k in kola:
        ranije = [r for r in R if r['kolo'] < k]
        if len(ranije) < 250:
            continue
        w = S.podesi_vreme(ranije)
        wf = []
        for k2 in sorted({r['kolo'] for r in ranije}):
            rr = [r for r in ranije if r['kolo'] < k2]
            if len(rr) < 250:
                continue
            w2 = S.podesi_vreme(rr)
            wf += [dict(s=r['s'], p=S.preko(w2, r['s'], r['pm'], r['tr']), y=r['preko']) for r in ranije if r['kolo'] == k2]
        kal = {s: S.platt([x for x in wf if x['s'] == s]) for s in 'PSA'} if len(wf) > 200 else None
        po_g = collections.defaultdict(list)
        for r in R:
            if r['kolo'] != k:
                continue
            x = info[(r['k'], r['dan'])]
            p = S.preko(w, r['s'], r['pm'], r['tr'])
            for strana, pp, kv, ok in (('o', p, r['o'], r['preko'] == 1), ('u', 1 - p, r['u'], r['preko'] == 0)):
                po_g[(x['g'], r['dan'])].append(dict(igr=r['k'], tim=x['team'], s=r['s'], strana=strana, pp=pp, ev=pp * kv - 1,
                                                    k=kv, l=r['l'], prosao=ok, dan=r['dan'], g=x['g'], kolo=k))
        stari = (S.PLUS_MIN, S.MIN_UT); S.PLUS_MIN, S.MIN_UT = plus_min, min_ut
        for (g, dan), C in po_g.items():
            for c in S.izbor_utakmice(C):
                po = c['pp'] if c['strana'] == 'o' else 1 - c['pp']
                pk = S.kalibrisi(po, kal, c['s']) if kal else po
                out[dan].append(dict(c, kvota=c['k'], k=c['igr'], kal=pk if c['strana'] == 'o' else 1 - pk))
        S.PLUS_MIN, S.MIN_UT = stari
    return out


def novi_dan(P, prag, najmanje=4, najvise=12, plus_n=0, plus_prag=0.56):
    P = sorted([dict(p, pp=p['kal'], forma=list(PR.forma(B, p))) for p in P if p.get('nivo') != 'slab'], key=lambda p: -p['pp'])
    P = [p for p in P if p['forma'][1] < 4 or p['forma'][0] / p['forma'][1] >= PR.DAN_FORMA_MIN]
    izab = []
    for p in P:
        if len(izab) >= najvise:
            break
        if (sum(q['g'] == p['g'] for q in izab) < 4 and sum(q['tim'] == p['tim'] for q in izab) < 2
                and (p['pp'] >= prag or len(izab) < najmanje)):
            izab.append(p)
    # poželjan PLUS (Nikola, 6.11.): ako ih ima manje od plus_n, dodaju se najbolji PLUS sa kal ≥ plus_prag
    for p in P:
        if sum(q['strana'] == 'o' for q in izab) >= plus_n:
            break
        if (p['strana'] == 'o' and p not in izab and p['pp'] >= plus_prag and sum(q['g'] == p['g'] for q in izab) < 4
                and sum(q['tim'] == p['tim'] for q in izab) < 2):
            izab.append(p)
    return izab


def z(X):
    if not X:
        return '—'
    n = len(X); pr = sum(x['prosao'] for x in X); d = sum((x['kvota'] - 1) if x['prosao'] else -1 for x in X)
    return f"{pr}/{n} {pr / n:.1%} {d / n:+.1%}"


rez = {}
staro = pools(2, 6)
P = []
for dan, C in staro.items():
    P += PR.izbor_dana([dict(c, pp=c['kal']) for c in C], B)
rez['sada (8 za dan, PLUS obavezan)'] = (P, len(staro))
novo = pools(0, 0)
for prag, plus_n, plus_prag in ((0.56, 0, 0), (0.58, 0, 0), (0.60, 0, 0), (0.62, 0, 0), (0.58, 1, 0.56), (0.58, 2, 0.56),
                               (0.58, 1, 0.54), (0.60, 1, 0.56)):
    P = []
    for dan, C in novo.items():
        P += novi_dan(C, prag, plus_n=plus_n, plus_prag=plus_prag)
    rez[f'novo: prag {prag:.2f}' + (f', PLUS do {plus_n} od {plus_prag:.2f}' if plus_n else '')] = (P, len(novo))
for ime, (P, n_dana) in rez.items():
    pl = [p for p in P if p['strana'] == 'o']; mi = [p for p in P if p['strana'] == 'u']
    print(f"{ime:34} {len(P) / n_dana:4.1f}/dan | {z(P)} | PLUS {z(pl)} | MINUS {z(mi)}")
