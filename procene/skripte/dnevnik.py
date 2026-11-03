"""Ishodi za dnevnik procena i kratak pregled tačnosti.

  python3 procene/skripte/dnevnik.py --kolo 11

Posle kola (kad razgovor za minuse ažurira baza/rows.json) upisuje stvarni učinak u
procene/dnevnik/kolo<N>.json i ispisuje: koliko učinaka je upalo u raspon, i na granicama
kladionica tačnost modela naspram kvota, posebno za preko i za ispod.
"""
import argparse, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from model import Baza
from zajedno import PROCENE, ucitaj, sacuvaj


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int, required=True)
    a = ap.parse_args()
    put = os.path.join(PROCENE, 'dnevnik', f'kolo{a.kolo}.json')
    dn = ucitaj(put)
    B = Baza()
    ish = {(r['g'], r['k']): r for r in B.rows}
    n = u50 = u80 = 0
    lin = []
    for x in dn['stavke']:
        r = ish.get((x['g'], x['k']))
        if not r:
            x['ishod'] = None          # nije igrao ili utakmica još nije u bazi
            continue
        y = r[x['s']]
        x['ishod'] = y; x['min_stvarno'] = round(r['min'], 1)
        q = x['q']; n += 1; u50 += q[1] <= y <= q[3]; u80 += q[0] <= y <= q[4]
        for z in x['linije']:
            lin.append((z, 1 if y > z['l'] else 0))
    sacuvaj(put, dn, kompaktno=True)
    print(f'kolo {a.kolo}: procena sa ishodom {n} od {len(dn["stavke"])}')
    if n:
        print(f'  u rasponu 25.-75.: {u50/n:.1%}, 10.-90.: {u80/n:.1%}')
    if lin:
        k = len(lin)
        print(f'  granica {k}: stvarno preko {sum(y for _, y in lin)/k:.1%}, model {sum(z["pm"] for z, _ in lin)/k:.1%}, kvote {sum(z["tr"] for z, _ in lin)/k:.1%}')
        print(f'  log gubitak model {sum(ll(z["pm"], y) for z, y in lin)/k:.4f}, kvote {sum(ll(z["tr"], y) for z, y in lin)/k:.4f}')
        for strana in ('ispod', 'preko'):
            igr = []
            for z, y in lin:
                evu = (1 - z['pm']) * z['u'] - 1; evo = z['pm'] * z['o'] - 1
                if strana == 'ispod' and evu > 0.05 and evu >= evo:
                    igr.append(z['u'] - 1 if y == 0 else -1)
                if strana == 'preko' and evo > 0.05 and evo > evu:
                    igr.append(z['o'] - 1 if y == 1 else -1)
            if igr:
                print(f'  model {strana} (prednost >5%): {len(igr)} granica, povraćaj {sum(igr)/len(igr):+.1%}')


if __name__ == '__main__':
    main()
