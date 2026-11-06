"""Kladionice: ko najbolje procenjuje, ko pobeđuje kad se granice razlikuju i da li kretanje kvota nešto znači.

  python3 procene/skripte/knjige.py            izveštaj na svim snimcima sa ishodom (procene/provera/knjige.md)
  python3 procene/skripte/knjige.py --dan D    samo kretanja i razlike za dan D (za presek pre objave)

Snimci: baza/ponude/<kladionica>/<dan>_<slovo>.json (prvi i poslednji snimak dana), samo glavne granice.
Fer verovatnoća = kvote bez marže. Ishodi iz zapisnika (baza/rows.json + dopuna).
"""
import argparse, collections, datetime as dt, glob, json, math, os, re, statistics as st, sys
sys.path.insert(0, os.path.dirname(__file__))
from model import Baza
from zajedno import BAZA, PROCENE, BG, kljuc_snimka, ucitaj, tim
import provera

KL = ('admiral', 'maxbet', 'mozzart', 'soccerbet')


def snimci():
    """{(kladionica, dan): [snimak po redu]} sa (vreme, picks)."""
    out = collections.defaultdict(list)
    for kl in KL:
        for f in sorted(glob.glob(os.path.join(BAZA, 'ponude', kl, '*.json')), key=kljuc_snimka):
            m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(f))
            j = ucitaj(f)
            if not m or 'picks' not in j:
                continue
            out[(kl, m.group(1))].append((j.get('at', ''), j['picks']))
    return out


def glavne(picks, kl, rez_dan):
    L = {}
    for p in picks:
        if p.get('s') not in ('P', 'S', 'A') or not p.get('u') or not p.get('o'):
            continue
        if 'm' in p and not p['m']:
            continue
        dan = provera.dan_iz_vremena(p.get('time'), rez_dan)
        tk = p.get('tk') or (None if ' | ' in (p.get('t') or '') else tim(p.get('t')))
        L[(p['p'], p['s'])] = dict(p=p['p'], t=p.get('t'), tk=tk, s=p['s'], l=p['l'], u=p['u'], o=p['o'], dan=dan,
                                   fer=(1 / p['o']) / (1 / p['u'] + 1 / p['o']), marza=1 / p['u'] + 1 / p['o'] - 1)
    return L


def ucitaj_sve(B):
    """Lista zapisa: igrač, dan, stavka, po kladionici prvi i poslednji snimak, ishod (ako je igrao)."""
    S = snimci()
    zap = {}
    for (kl, d), sn in S.items():
        prvi, posl = glavne(sn[0][1], kl, d), glavne(sn[-1][1], kl, d)
        for key, x in posl.items():
            k, _ = B.nadji_u_utakmici(x['p'], x.get('t'), x['tk'])
            if not k:
                continue
            id_ = (k, x['dan'], x['s'])
            z = zap.setdefault(id_, dict(k=k, dan=x['dan'], s=x['s'], kl={}))
            z['kl'][kl] = dict(posl=x, prvi=prvi.get(key), n_snimaka=len(sn), vremena=(sn[0][0], sn[-1][0]))
    for z in zap.values():
        r = [r for r in B.byk.get(z['k'], []) if r['dan'] == z['dan']]
        z['ishod'] = r[0][z['s']] if r else None
    return list(zap.values())


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def izvestaj(Z):
    L = ['# Kladionice: tačnost, razlike granica, kretanje kvota', '',
         f'Zapisa sa ishodom: {sum(1 for z in Z if z["ishod"] is not None)}. Uzorak sa više kladionica je mali (od 4.11.2026); izveštaj se osvežava sa svakim danom.', '']
    Y = [z for z in Z if z['ishod'] is not None]
    L += ['## 1. Svaka kladionica na svojim granicama (poslednji snimak dana)', '',
          '| kladionica | granica | marža | log gubitak | stvarno preko | fer preko |', '|---|---|---|---|---|---|']
    for kl in KL:
        X = [(z['kl'][kl]['posl'], z['ishod']) for z in Y if kl in z['kl']]
        if not X:
            continue
        yy = [1 if i > x['l'] else 0 for x, i in X]
        L.append(f"| {kl} | {len(X)} | {st.mean(x['marza'] for x, _ in X):.1%} | {st.mean(ll(x['fer'], y) for (x, _), y in zip(X, yy)):.4f} | "
                 f"{st.mean(yy):.1%} | {st.mean(x['fer'] for x, _ in X):.1%} |")
    # zajednički skup: iste granice kod svih kladionica u paru
    L += ['', '## 2. Parovi na istoj granici (ista igrač, stavka, dan, granica): čija fer verovatnoća je tačnija', '',
          '| par | granica | log gubitak A | log gubitak B |', '|---|---|---|---|']
    for i, a in enumerate(KL):
        for b in KL[i + 1:]:
            X = [(z['kl'][a]['posl'], z['kl'][b]['posl'], z['ishod']) for z in Y if a in z['kl'] and b in z['kl']
                 and z['kl'][a]['posl']['l'] == z['kl'][b]['posl']['l']]
            if len(X) >= 20:
                yy = [1 if i_ > x['l'] else 0 for x, _, i_ in X]
                L.append(f"| {a} – {b} | {len(X)} | {st.mean(ll(x['fer'], y) for (x, _, _), y in zip(X, yy)):.4f} | "
                         f"{st.mean(ll(w['fer'], y) for (_, w, _), y in zip(X, yy)):.4f} |")
    # razlike granica
    R = []
    for z in Y:
        ls = {kl: v['posl']['l'] for kl, v in z['kl'].items()}
        if len(set(ls.values())) > 1:
            lo, hi = min(ls.values()), max(ls.values())
            klo = [k for k, v in ls.items() if v == lo]; khi = [k for k, v in ls.items() if v == hi]
            o_lo = z['kl'][klo[0]]['posl']['o']; u_hi = z['kl'][khi[0]]['posl']['u']
            R.append(dict(lo=lo, hi=hi, klo=klo, khi=khi, o_lo=o_lo, u_hi=u_hi, i=z['ishod'], z=z))
    L += ['', f'## 3. Kad se granice razlikuju ({len(R)} slučajeva)', '']
    if R:
        pl = sum(1 for r in R if r['i'] > r['lo']); mi = sum(1 for r in R if r['i'] < r['hi'])
        dob_o = sum((r['o_lo'] - 1) if r['i'] > r['lo'] else -1 for r in R)
        dob_u = sum((r['u_hi'] - 1) if r['i'] < r['hi'] else -1 for r in R)
        L.append(f'- PREKO na najnižoj granici: prošlo {pl}/{len(R)}, povraćaj {dob_o / len(R):+.1%}')
        L.append(f'- ISPOD na najvišoj granici: prošlo {mi}/{len(R)}, povraćaj {dob_u / len(R):+.1%}')
        cnt = collections.Counter(k for r in R for k in r['klo'])
        cnt2 = collections.Counter(k for r in R for k in r['khi'])
        L.append(f'- Najniža granica najčešće kod: {dict(cnt)}; najviša: {dict(cnt2)}')
        for kl in KL:
            X = [r for r in R if kl in r['klo'] and len(r['klo']) == 1]
            if X:
                L.append(f'  - {kl} sam ima najnižu granicu: {len(X)}, preko prošlo {sum(r["i"] > r["lo"] for r in X)}')
            X = [r for r in R if kl in r['khi'] and len(r['khi']) == 1]
            if X:
                L.append(f'  - {kl} sam ima najvišu granicu: {len(X)}, ispod prošlo {sum(r["i"] < r["hi"] for r in X)}')
    # kretanje
    M = []
    for z in Y:
        for kl, v in z['kl'].items():
            a, b = v['prvi'], v['posl']
            if not a or v['n_snimaka'] < 2:
                continue
            if a['l'] != b['l']:
                M.append(dict(kl=kl, vrsta='granica', smer='gore' if b['l'] > a['l'] else 'dole', y=z['ishod'] > b['l'], l=b['l'], o=b['o'], u=b['u']))
            elif abs(b['fer'] - a['fer']) >= 0.03:
                M.append(dict(kl=kl, vrsta='kvota', smer='gore' if b['fer'] > a['fer'] else 'dole', y=z['ishod'] > b['l'], l=b['l'], o=b['o'], u=b['u']))
    L += ['', f'## 4. Kretanje u toku dana, prvi → poslednji snimak ({len(M)} pomeranja)', '',
          '„gore“ = granica porasla ili verovatnoća za preko porasla. Pitanje: da li ishod ide u smeru pomeranja.', '']
    for vr in ('granica', 'kvota'):
        for sm in ('gore', 'dole'):
            X = [m for m in M if m['vrsta'] == vr and m['smer'] == sm]
            if X:
                sa = sum(m['y'] if sm == 'gore' else not m['y'] for m in X)
                L.append(f'- {vr} {sm}: {len(X)}, ishod u smeru pomeranja {sa}/{len(X)} ({sa / len(X):.0%})')
    for kl in KL:
        X = [m for m in M if m['kl'] == kl]
        if X:
            sa = sum(m['y'] if m['smer'] == 'gore' else not m['y'] for m in X)
            L.append(f'  - {kl}: {len(X)} pomeranja, u smeru {sa}')
    return '\n'.join(L)


def dan_pregled(Z, dan):
    L = [f'Kladionice za {dan}:']
    Dz = [z for z in Z if z['dan'] == dan]
    raz = [z for z in Dz if len({v['posl']['l'] for v in z['kl'].values()}) > 1]
    L.append(f'  razlike granica ({len(raz)}):')
    for z in sorted(raz, key=lambda z: z['k']):
        L.append(f"    {z['k']} {z['s']}: " + ', '.join(f"{kl} {v['posl']['l']} ({v['posl']['u']}/{v['posl']['o']})" for kl, v in sorted(z['kl'].items())))
    mv = []
    for z in Dz:
        for kl, v in z['kl'].items():
            a, b = v['prvi'], v['posl']
            if a and (a['l'] != b['l'] or abs(a['fer'] - b['fer']) >= 0.03):
                mv.append(f"    {z['k']} {z['s']} {kl}: {a['l']} ({a['u']}/{a['o']}) → {b['l']} ({b['u']}/{b['o']})")
    L.append(f'  kretanja u toku dana ({len(mv)}):')
    L += sorted(mv)
    return '\n'.join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dan')
    a = ap.parse_args()
    B = Baza()
    Z = ucitaj_sve(B)
    if a.dan:
        print(dan_pregled(Z, a.dan))
        return
    t = izvestaj(Z)
    with open(os.path.join(PROCENE, 'provera', 'knjige.md'), 'w') as f:
        f.write(t + '\n')
    print(t)


if __name__ == '__main__':
    main()
