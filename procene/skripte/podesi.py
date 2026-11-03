"""Podešavanje parametara modela na verodostojnost učinaka (ne na ponudama).

  python3 procene/skripte/podesi.py [--do-kola 6]

Cilj: zbir log verovatnoća stvarnih P, S, A za sve igrače sa bar 2 prethodne utakmice,
u kolima 3 do --do-kola. Pretraga po koordinatama. Rezultat ide u procene/model_parametri.json.
"""
import argparse, copy, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import model
from model import Baza, PAR, log_ver
from zajedno import sacuvaj, PROCENE


def cilj(B, mete, par, stavke='PSA'):
    model.PAR.update(par)
    tot = {s: 0.0 for s in stavke}
    for r in mete:
        e = B.procena(r['k'], r['dan'], r['team'], r['opp'], minuti=None, pos=r['pos'] if r['pos'] in 'GFC' else None)
        if not e:
            continue
        for s in stavke:
            x = e['s'][s]
            tot[s] += log_ver(x['mu'], x['var'], r[s])
    return tot


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--od-kola', type=int, default=3)
    ap.add_argument('--do-kola', type=int, default=6)
    arg = ap.parse_args()
    B = Baza()
    mete = [r for r in B.rows if arg.od_kola <= r['r'] <= arg.do_kola
            and len([x for x in B.byk[r['k']] if x['dan'] < r['dan']]) >= 2]
    print('meta učinaka', len(mete))
    par = copy.deepcopy(PAR)
    zajednicki = {'DM': [0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], 'DR': [0.75, 0.82, 0.88, 0.94, 1.0], 'CV': [0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0],
                  'K2': [50, 100, 150, 250, 400], 'MW': [0.0, 0.5, 1.0, 2.0, 3.0]}
    po_stavci = {'K': [10, 20, 40, 60, 90, 130, 200, 300, 450, 650], 'B_OF': [0.0, 0.25, 0.5, 0.75, 1.0],
                 'B_TEMPO': [0.0, 0.3, 0.6, 1.0], 'A': [0.8, 1.0, 1.2, 1.5, 1.8, 2.2, 2.6, 3.0, 3.5, 4.0, 5.0],
                 'C': [0.0, 0.02, 0.04, 0.06, 0.1, 0.15, 0.22, 0.3]}
    najbolje = sum(cilj(B, mete, par).values())
    print('početno', round(najbolje, 1))
    for krug in range(3):
        for kl, vr in zajednicki.items():
            for v in vr:
                p2 = copy.deepcopy(par); p2[kl] = v
                c = sum(cilj(B, mete, p2).values())
                if c > najbolje + 0.05:
                    najbolje, par = c, p2
            print(krug, kl, par[kl], round(najbolje, 1))
        for s in 'PSA':
            for kl, vr in po_stavci.items():
                osnova = cilj(B, mete, par, s)[s]
                for v in vr:
                    p2 = copy.deepcopy(par); p2[kl] = dict(par[kl]); p2[kl][s] = v
                    c = cilj(B, mete, p2, s)[s]
                    if c > osnova + 0.05:
                        osnova, par = c, p2
                print(krug, s, kl, par[kl][s])
            najbolje = sum(cilj(B, mete, par).values())
        print('krug', krug, 'ukupno', round(najbolje, 1))
    # doterivanje verovatnoća: veštačke granice oko očekivanja, za svaki učinak u kolima podešavanja
    model.PAR.update(par)
    par['KAL'] = {}
    for s in 'PSA':
        X, Y = [], []
        for r in mete:
            e = B.procena(r['k'], r['dan'], r['team'], r['opp'])
            if not e:
                continue
            mu, var = e['s'][s]['mu'], e['s'][s]['var']
            q10, _, _, _, q90 = model.percentili(mu, var)
            for q in range(max(0, q10 - 1), q90 + 1):
                p = min(max(model.p_preko(mu, var, q + 0.5), 1e-4), 1 - 1e-4)
                X.append(math.log(p / (1 - p))); Y.append(1 if r[s] > q + 0.5 else 0)
        a, b = 0.0, 1.0
        for _ in range(25):   # Njutn za logističku regresiju sa jednim prediktorom
            g0 = g1 = h00 = h01 = h11 = 0.0
            for x, y in zip(X, Y):
                pp = 1 / (1 + math.exp(-(a + b * x))); w = pp * (1 - pp); d = y - pp
                g0 += d; g1 += d * x; h00 += w; h01 += w * x; h11 += w * x * x
            det = h00 * h11 - h01 * h01
            a += (h11 * g0 - h01 * g1) / det; b += (h00 * g1 - h01 * g0) / det
        par['KAL'][s] = [round(a, 4), round(b, 4)]
        print('doterivanje', s, par['KAL'][s], 'tačaka', len(X))
    par['_podeseno'] = f'kola {arg.od_kola}-{arg.do_kola}, {len(mete)} učinaka, log ver {round(najbolje, 1)}'
    sacuvaj(os.path.join(PROCENE, 'model_parametri.json'), par)
    print(json.dumps(par, ensure_ascii=False))


if __name__ == '__main__':
    main()
