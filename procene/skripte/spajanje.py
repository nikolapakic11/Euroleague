"""Spojena verovatnoća: model + kvote, podešeno prema stvarnim ishodima na granicama.

  python3 procene/skripte/spajanje.py      (posle provera.py)

Model sam je previše samouveren (kad kaže 67%, prolazi oko 58%), a kvote sistematski precenjuju preko.
Zato se verovatnoća za preko računa kao
  logit p = a + b·logit(model) + c·logit(kvote bez marže) + d_S·[skokovi] + d_A·[asistencije]
sa koeficijentima iz logističke regresije na granicama iz procene/provera/granice.json.
Ista formula važi za obe strane (ispod = 1 − p), pa preko i ispod imaju jednake uslove.

Izlaz procene/spajanje.json:
  w      koeficijenti podešeni na svim granicama (za predloge i tablu)
  test   isto pravilo za predloge, podešeno na kolima 4–6 i provereno na kolima 7–9 (van podešavanja)
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, ucitaj, sacuvaj

# pravilo za predloge (koristi ga i predlozi.py)
P_MIN = 0.55        # spojena verovatnoća izabrane strane
EV_MIN = 0.10       # spojena verovatnoća × kvota − 1
KVOTA_MIN = 1.40


def lg(p):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return math.log(p / (1 - p))


def x_vek(s, pm, tr):
    return [1.0, lg(pm), lg(tr), 1.0 if s == 'S' else 0.0, 1.0 if s == 'A' else 0.0]


def preko(w, s, pm, tr):
    z = sum(a * b for a, b in zip(w, x_vek(s, pm, tr)))
    return 1 / (1 + math.exp(-z))


def podesi(R, l2=1.0):
    d = 5
    w = [0.0] * d
    for _ in range(40):
        g = [0.0] * d
        H = [[0.0] * d for _ in range(d)]
        for r in R:
            x = x_vek(r['s'], r['pm'], r['tr'])
            p = 1 / (1 + math.exp(-sum(a * b for a, b in zip(w, x))))
            y = r['preko']
            for i in range(d):
                g[i] += (y - p) * x[i]
                for j in range(d):
                    H[i][j] += p * (1 - p) * x[i] * x[j]
        for i in range(1, d):
            g[i] -= l2 * w[i]; H[i][i] += l2
        A = [H[i][:] + [g[i]] for i in range(d)]
        for c in range(d):
            piv = max(range(c, d), key=lambda q: abs(A[q][c]))
            A[c], A[piv] = A[piv], A[c]
            for q in range(d):
                if q != c:
                    f = A[q][c] / A[c][c]
                    A[q] = [a - f * b for a, b in zip(A[q], A[c])]
        w = [a + A[i][d] / A[i][i] for i, a in enumerate(w)]
    return [round(a, 4) for a in w]


def izbor(kandidati):
    """kandidati: dict(kljuc_igraca, pp, ev, k, ...). Jedan po igraču: najizglednija strana/granica."""
    best = {}
    for c in kandidati:
        if c['pp'] >= P_MIN and c['ev'] >= EV_MIN and c['k'] >= KVOTA_MIN:
            if c['id'] not in best or (c['pp'], c['ev']) > (best[c['id']]['pp'], best[c['id']]['ev']):
                best[c['id']] = c
    return list(best.values())


def predlozi_unazad(w, R):
    kand = []
    for r in R:
        p = preko(w, r['s'], r['pm'], r['tr'])
        kand.append(dict(id=(r['dan'], r['k']), strana='o', pp=p, ev=p * r['o'] - 1, k=r['o'], prosao=r['preko'] == 1, kolo=r['kolo'], s=r['s']))
        kand.append(dict(id=(r['dan'], r['k']), strana='u', pp=1 - p, ev=(1 - p) * r['u'] - 1, k=r['u'], prosao=r['preko'] == 0, kolo=r['kolo'], s=r['s']))
    return izbor(kand)


def main():
    R = ucitaj(os.path.join(PROCENE, 'provera', 'granice.json'))
    w_sve = podesi(R)
    tr = [r for r in R if r['kolo'] <= 6]
    te = [r for r in R if r['kolo'] >= 7]
    w_tr = podesi(tr)
    P = predlozi_unazad(w_tr, te)
    po_kolu = {}
    for x in P:
        a = po_kolu.setdefault(x['kolo'], dict(kolo=x['kolo'], n=0, prosao=0, dobit=0.0, preko=0, ispod=0, P=0, S=0, A=0))
        a['n'] += 1; a['prosao'] += x['prosao']; a['dobit'] += (x['k'] - 1) if x['prosao'] else -1
        a['preko' if x['strana'] == 'o' else 'ispod'] += 1; a[x['s']] += 1
    kola = [dict(v, dobit=round(v['dobit'], 2)) for _, v in sorted(po_kolu.items())]
    ll = lambda p, y: -(y * math.log(p) + (1 - y) * math.log(1 - p))
    test = dict(opis='koeficijenti iz kola 4–6, predlozi na kolima 7–9 (van podešavanja); Admiral i MaxBet, jedna kladionica po danu',
                kola=kola, n=len(P), prosao=sum(x['prosao'] for x in P), dobit=round(sum((x['k'] - 1) if x['prosao'] else -1 for x in P), 2),
                preko=sum(x['strana'] == 'o' for x in P),
                ll_spojeno=round(sum(ll(preko(w_tr, r['s'], r['pm'], r['tr']), r['preko']) for r in te) / len(te), 4),
                ll_kvote=round(sum(ll(min(max(r['tr'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4),
                ll_model=round(sum(ll(min(max(r['pm'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4))
    out = dict(w=w_sve, w_kola_4_6=w_tr, n_granica=len(R), pravilo=dict(p_min=P_MIN, ev_min=EV_MIN, kvota_min=KVOTA_MIN), test=test)
    sacuvaj(os.path.join(PROCENE, 'spajanje.json'), out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
