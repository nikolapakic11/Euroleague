"""Ko zaista dobija kad rotacioni igrač ne igra, i kad se važan igrač vrati (analiza 6.11.2026).

  python3 procene/provera/odsustvo_2026-11-06.py

Na svim zapisnicima sezone (baza/rows.json + dopuna). Za svaku utakmicu tima:
  odsutan = igrao bar polovinu ranijih utakmica tima, bar 15 min u proseku, bar jednu od poslednje 3, a sad ne igra.
Za prisutne saigrače (bar 3 ranije utakmice) poredi se učinak sa njihovim prosekom pre te utakmice
(zbir stvarnog / zbir proseka), po ulozi:
  - rang u timu po poenima u proseku (1 = glavna opcija među prisutnima)
  - ista pozicija kao odsutni: prvi po minutima (direktna zamena) i ostali
Osnova: utakmice istih igrača bez odsutnih.
"""
import collections, json, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte'))
os.chdir(KOREN)
from model import Baza

B = Baza()
po_g = collections.defaultdict(lambda: collections.defaultdict(list))
for r in B.rows:
    po_g[r['team']][r['g']].append(r)
red_g = {t: sorted(G, key=lambda g: G[g][0]['d']) for t, G in po_g.items()}

zbir = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0]))   # grupa -> stavka -> [stvarno, prosek, n]


def dodaj(grupa, r, h):
    for s in ('min', 'P', 'S', 'A'):
        a = zbir[grupa][s]
        a[0] += r[s]; a[1] += st.mean(x[s] for x in h); a[2] += 1


for t, G in red_g.items():
    for idx, g in enumerate(G):
        ranije = G[:idx]
        if len(ranije) < 3:
            continue
        sada = {r['k']: r for r in po_g[t][g]}
        ist = collections.defaultdict(list)
        for gg in ranije:
            for r in po_g[t][gg]:
                ist[r['k']].append(r)
        van = []
        for k, h in ist.items():
            if k in sada:
                continue
            if len(h) >= 0.5 * len(ranije) and st.mean(x['min'] for x in h) >= 15 and any(
                    k in {r['k'] for r in po_g[t][gg]} for gg in ranije[-3:]):
                van.append((k, h[-1]['pos'], st.mean(x['min'] for x in h), st.mean(x['P'] for x in h)))
        prisutni = [(k, ist[k]) for k in sada if len(ist.get(k, [])) >= 3]
        rang = {k: i for i, (k, h) in enumerate(sorted(prisutni, key=lambda kh: -st.mean(x['P'] for x in kh[1])), 1)}
        if not van:
            for k, h in prisutni:
                dodaj(f'osnova rang {min(rang[k], 4)}', sada[k], h)
            continue
        poz_van = {p for _, p, _, _ in van}
        min_van = sum(m for _, _, m, _ in van)
        zbir['_info']['odsutan'][2] += len(van)
        for k, h in prisutni:
            r = sada[k]
            pos = h[-1]['pos']
            dodaj(f'odsustvo rang {min(rang[k], 4)}', r, h)
            if pos in poz_van:
                ista = sorted([kk for kk, hh in prisutni if hh[-1]['pos'] == pos], key=lambda kk: -st.mean(x['min'] for x in ist[kk]))
                dodaj('odsustvo ista poz: 1. po minutima' if ista and ista[0] == k else 'odsustvo ista poz: ostali', r, h)
            else:
                dodaj('odsustvo druga poz', r, h)
            # glavna opcija i direktna zamena zajedno
            ista = sorted([kk for kk, hh in prisutni if hh[-1]['pos'] in poz_van], key=lambda kk: -st.mean(x['min'] for x in ist[kk]))
            if rang[k] == 1 or (ista and ista[0] == k):
                dodaj('odsustvo: glavna opcija ili direktna zamena', r, h)
            else:
                dodaj('odsustvo: svi ostali', r, h)

# povratak: važan igrač (≥20 min) propustio ≥2 i vratio se u poslednjih 1–5; saigrači u utakmicama posle povratka
pov = collections.defaultdict(lambda: collections.defaultdict(lambda: [0.0, 0.0, 0]))
for t, G in red_g.items():
    for idx, g in enumerate(G):
        ranije = G[:idx]
        if len(ranije) < 4:
            continue
        ist = collections.defaultdict(list)
        for gg in ranije:
            for r in po_g[t][gg]:
                ist[r['k']].append(r)
        sada = {r['k']: r for r in po_g[t][g]}
        for k, h in ist.items():
            if k not in sada or st.mean(x['min'] for x in h) < 20:
                continue
            igrao = [k in {r['k'] for r in po_g[t][gg]} for gg in ranije]
            posle = 0
            for x in reversed(igrao):
                if x: posle += 1
                else: break
            propustio = igrao.count(False)
            if not (0 <= posle <= 4 and propustio >= 2 and (posle > 0 or not igrao[-1])):
                continue
            grupa = f'povratak, {posle + 1}. utakmica posle'
            for kk, hh in ist.items():
                if kk == k or kk not in sada or len(hh) < 3:
                    continue
                for s in ('min', 'P', 'S', 'A'):
                    a = pov[grupa][s]; a[0] += sada[kk][s]; a[1] += st.mean(x[s] for x in hh); a[2] += 1
            break

out = {}
print('odsutnih slučajeva', zbir['_info']['odsutan'][2])
for grupa in sorted(g for g in zbir if g != '_info'):
    v = zbir[grupa]
    out[grupa] = {s: dict(odnos=round(a[0] / a[1], 3) if a[1] else None, n=a[2]) for s, a in v.items()}
    print(f"{grupa:48} n={v['min'][2]:4}  " + '  '.join(f"{s} {a[0] / a[1]:.2f}" for s, a in v.items()))
for grupa in sorted(pov):
    v = pov[grupa]
    out[grupa] = {s: dict(odnos=round(a[0] / a[1], 3), n=a[2]) for s, a in v.items()}
    print(f"{grupa:48} n={v['min'][2]:4}  " + '  '.join(f"{s} {a[0] / a[1]:.2f}" for s, a in v.items()))
json.dump(out, open('procene/provera/odsustvo_2026-11-06.json', 'w'), ensure_ascii=False, indent=1)
