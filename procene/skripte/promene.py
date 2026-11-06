"""Fundamenti: šta se promenilo u poslednjih 2–3 utakmice (Nikola, 6.11.2026: npr. Walker, Koloko u Zvezdi).

  python3 procene/skripte/promene.py [--dan 2026-11-06] [--n 3]

Za svaki tim koji igra tog dana poredi poslednje N utakmica sa ranijim delom sezone:
  - tim: postignuti i primljeni poeni, skokovi i asistencije koje dozvoljava, ritam (zbir poena)
  - novi igrači (prvi meč za tim u poslednjih N): minuti, učinak i kako je tim igrao sa njima i bez njih
  - igrači kojima su se minuti promenili za bar 5 (veća ili manja uloga), i ko od rotacije nije igrao
Ovo nije u modelu; služi za dubinsku analizu pre predloga (RAD.md) i ispisuje se u preseku.
"""
import argparse, collections, datetime as dt, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(__file__))
from model import Baza
from zajedno import BG, utakmice


def tim_utakmice(B, kod, dan):
    po_g = collections.defaultdict(list)
    for r in B.rows:
        if r['team'] == kod and r['dan'] < dan:
            po_g[r['g']].append(r)
    prot = collections.defaultdict(list)
    for r in B.rows:
        if r['g'] in po_g and r['team'] != kod:
            prot[r['g']].append(r)
    G = sorted(po_g, key=lambda g: po_g[g][0]['d'])
    return G, po_g, prot


def zbir_tima(G, po_g, prot):
    if not G:
        return None
    f = lambda L, s: sum(r[s] for r in L)
    return dict(n=len(G), za=st.mean(f(po_g[g], 'P') for g in G), protiv=st.mean(f(prot[g], 'P') for g in G),
                sk_protiv=st.mean(f(prot[g], 'S') for g in G), as_protiv=st.mean(f(prot[g], 'A') for g in G),
                sk=st.mean(f(po_g[g], 'S') for g in G), asi=st.mean(f(po_g[g], 'A') for g in G))


def analiza_tima(B, kod, dan, n=3):
    G, po_g, prot = tim_utakmice(B, kod, dan)
    if len(G) < n + 2:
        return None
    sv, rn = G[-n:], G[:-n]
    out = dict(tim=kod, sveze=zbir_tima(sv, po_g, prot), ranije=zbir_tima(rn, po_g, prot), novi=[], uloga=[], izostali=[])
    igr = collections.defaultdict(list)
    for g in G:
        for r in po_g[g]:
            igr[r['k']].append((g, r))
    for k, L in igr.items():
        prvi = L[0][0]
        ime = L[-1][1]['name']
        if prvi in sv:
            sa = [g for g, _ in L]
            bez = [g for g in G if g not in sa]
            out['novi'].append(dict(ime=ime, utakmica=len(L), min=[round(r['min']) for _, r in L],
                                    P=[r['P'] for _, r in L], S=[r['S'] for _, r in L], A=[r['A'] for _, r in L],
                                    sa=zbir_tima(sa, po_g, prot), bez=zbir_tima(bez, po_g, prot)))
            continue
        m_r = [r['min'] for g, r in L if g in rn]
        m_s = [r['min'] for g, r in L if g in sv]
        if len(m_r) >= 3 and m_s:
            d = st.mean(m_s) - st.mean(m_r)
            if abs(d) >= 5:
                out['uloga'].append(dict(ime=ime, ranije=round(st.mean(m_r), 1), sveze=round(st.mean(m_s), 1),
                                         P=(round(st.mean(r['P'] for g, r in L if g in rn), 1), round(st.mean(r['P'] for g, r in L if g in sv), 1))))
        if len(m_r) >= 0.6 * len(rn) and st.mean(m_r) >= 15 and len(m_s) < len(sv):
            out['izostali'].append(dict(ime=ime, min=round(st.mean(m_r), 1), propustio=len(sv) - len(m_s)))
    return out


def ispis(a):
    s, r = a['sveze'], a['ranije']
    red = lambda x: f"daje {x['za']:.0f}, prima {x['protiv']:.0f}, dozvoljava skokova {x['sk_protiv']:.0f} i asist. {x['as_protiv']:.0f}"
    L = [f"{a['tim']}: poslednje {s['n']}: {red(s)} | ranije ({r['n']}): {red(r)}"]
    for x in a['novi']:
        t = f"   NOV: {x['ime']} {x['utakmica']} utak., min {x['min']}, P {x['P']}, S {x['S']}, A {x['A']}"
        if x['sa'] and x['bez']:
            t += f" | tim sa njim prima {x['sa']['protiv']:.0f} i dozvoljava {x['sa']['sk_protiv']:.0f} skokova, bez njega {x['bez']['protiv']:.0f} i {x['bez']['sk_protiv']:.0f}"
        L.append(t)
    for x in sorted(a['uloga'], key=lambda x: x['ranije'] - x['sveze']):
        L.append(f"   ULOGA: {x['ime']} minuti {x['ranije']} → {x['sveze']}, poeni {x['P'][0]} → {x['P'][1]}")
    for x in a['izostali']:
        L.append(f"   NIJE IGRAO: {x['ime']} ({x['min']} min ranije) u {x['propustio']} od poslednjih {s['n']}")
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dan', default=dt.datetime.now(BG).date().isoformat())
    ap.add_argument('--n', type=int, default=3)
    a = ap.parse_args()
    B = Baza()
    for u in sorted([u for u in utakmice() if u['dan'] == a.dan], key=lambda u: u['utc']):
        print(f"\n{u['dom']}–{u['gost']}")
        for kod in (u['dom'], u['gost']):
            x = analiza_tima(B, kod, a.dan, a.n)
            print(ispis(x) if x else f'{kod}: premalo utakmica')


if __name__ == '__main__':
    main()
