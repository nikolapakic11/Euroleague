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

# pravila za predloge (koristi ih i predlozi.py)
KVOTA_MIN = 1.50
# MINUS (ispod): spojena verovatnoća i prednost
P_MIN = 0.55        # spojena verovatnoća za ispod
EV_MIN = 0.20       # spojena verovatnoća × kvota − 1
# PLUS (preko): kvote za preko su u oktobru bile preskupe, pa spojena verovatnoća skoro nikad ne pređe 55%.
# Preko zato ima svoje pravilo: model vidi preko za RAZ_MIN do RAZ_MAX više od kvota (bez marže).
# Veća razlika od toga je u proveri bila lošija (najčešće greška modela, npr. promena uloge igrača).
RAZ_MIN = 0.05
RAZ_MAX = 0.15


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


def prolazi(c):
    if c['k'] < KVOTA_MIN:
        return False
    if c['strana'] == 'u':
        return c['pp'] >= P_MIN and c['ev'] >= EV_MIN
    return RAZ_MIN <= c['raz'] < RAZ_MAX


def izbor(kandidati):
    """kandidati: dict(id igrača, strana, s, pp, ev, k, raz). Najviše jedan MINUS i jedan PLUS po igraču
    (MINUS: najizgledniji; PLUS: najveća razlika model − kvote), a PLUS ne ide na stavku koja već ima MINUS."""
    best = {}
    for c in kandidati:
        if not prolazi(c):
            continue
        kl = (c['id'], c['strana'])
        kljuc = (c['pp'], c['ev']) if c['strana'] == 'u' else (c['raz'], c['ev'])
        if kl not in best or kljuc > best[kl][0]:
            best[kl] = (kljuc, c)
    out = [c for _, c in best.values()]
    minus = {(c['id'], c['s']) for c in out if c['strana'] == 'u'}
    return [c for c in out if not (c['strana'] == 'o' and (c['id'], c['s']) in minus)]


def predlozi_unazad(w, R):
    kand = []
    for r in R:
        p = preko(w, r['s'], r['pm'], r['tr'])
        kand.append(dict(id=(r['dan'], r['k']), strana='o', pp=p, ev=p * r['o'] - 1, k=r['o'], raz=r['pm'] - r['tr'], prosao=r['preko'] == 1, kolo=r['kolo'], s=r['s']))
        kand.append(dict(id=(r['dan'], r['k']), strana='u', pp=1 - p, ev=(1 - p) * r['u'] - 1, k=r['u'], raz=r['tr'] - r['pm'], prosao=r['preko'] == 0, kolo=r['kolo'], s=r['s']))
    return izbor(kand)


def main():
    R = ucitaj(os.path.join(PROCENE, 'provera', 'granice.json'))
    w_sve = podesi(R)
    tr = [r for r in R if r['kolo'] <= 6]
    te = [r for r in R if r['kolo'] >= 7]
    w_tr = podesi(tr)
    P = predlozi_unazad(w_tr, te)
    def zbir(X):
        po_kolu = {}
        for x in X:
            a = po_kolu.setdefault(x['kolo'], dict(kolo=x['kolo'], n=0, prosao=0, dobit=0.0, P=0, S=0, A=0))
            a['n'] += 1; a['prosao'] += x['prosao']; a['dobit'] += (x['k'] - 1) if x['prosao'] else -1; a[x['s']] += 1
        kola = [dict(v, dobit=round(v['dobit'], 2)) for _, v in sorted(po_kolu.items())]
        return dict(kola=kola, n=len(X), prosao=sum(x['prosao'] for x in X),
                    dobit=round(sum((x['k'] - 1) if x['prosao'] else -1 for x in X), 2))
    po_strani = {'minus': zbir([x for x in P if x['strana'] == 'u']), 'plus': zbir([x for x in P if x['strana'] == 'o'])}
    # PLUS i na kolima 4–6 (pravilo za preko ne zavisi od spajanja, pa se može pokazati i tu)
    P46 = [x for x in predlozi_unazad(w_tr, tr) if x['strana'] == 'o']
    po_strani['plus_4_6'] = zbir(P46)
    ll = lambda p, y: -(y * math.log(p) + (1 - y) * math.log(1 - p))
    test = dict(opis='koeficijenti iz kola 4–6, predlozi na kolima 7–9 (van podešavanja); Admiral i MaxBet, jedna kladionica po danu',
                po_strani=po_strani,
                ll_spojeno=round(sum(ll(preko(w_tr, r['s'], r['pm'], r['tr']), r['preko']) for r in te) / len(te), 4),
                ll_kvote=round(sum(ll(min(max(r['tr'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4),
                ll_model=round(sum(ll(min(max(r['pm'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4))
    out = dict(w=w_sve, w_kola_4_6=w_tr, n_granica=len(R), pravilo=dict(p_min=P_MIN, ev_min=EV_MIN, kvota_min=KVOTA_MIN, raz_min=RAZ_MIN, raz_max=RAZ_MAX), test=test)
    sacuvaj(os.path.join(PROCENE, 'spajanje.json'), out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
