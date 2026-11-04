"""Spojena verovatnoća: model + kvote, podešeno prema stvarnim ishodima na granicama.

  python3 procene/skripte/spajanje.py      (posle provera.py)

Model sam je previše samouveren (kad kaže 67%, prolazi oko 58%), a kvote sistematski precenjuju preko.
Zato se verovatnoća za preko računa kao
  logit p = a + b·logit(model) + c·logit(kvote bez marže) + d_S·[skokovi] + d_A·[asistencije]
sa koeficijentima iz logističke regresije na granicama iz procene/provera/granice.json.
Ista formula važi za obe strane (ispod = 1 − p). Na njoj se zasniva izbor 4 do 6 predloga po utakmici (izbor_utakmice).

Izlaz procene/spajanje.json:
  w      koeficijenti podešeni na svim granicama (za predloge i tablu)
  test   pravilo predloga na ranijim ponudama: kola 7–9 van podešavanja, kola 4–6 u periodu podešavanja
"""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, ucitaj, sacuvaj

# pravila za predloge (koriste ih tabla.py i predlozi.py)
KVOTA_MIN = 1.50
# Po utakmici 4 do 6 predloga, rangirano po spojenoj verovatnoći izabrane strane.
# Strana ulazi ako joj je spojena verovatnoća bar PRAG (PLUS ima niži prag jer kvote sistematski precenjuju preko,
# pa spojena verovatnoća za preko retko pređe 55%). Ako ih je manje od MIN_UT, dopunjava se najboljim ispod praga („slab“).
PRAG = {'u': 0.53, 'o': 0.50}
MIN_UT, MAX_UT = 4, 6
PLUS_MIN = 2            # do 2 PLUS po utakmici dobijaju mesto unapred, ako prolaze prag
NIVOI = ((0.60, 'jak'), (0.55, 'solidan'))      # ispod 0,55 a iznad praga: „nagoveštaj“


def nivo(pp, slab=False):
    if slab:
        return 'slab'
    for granica, ime in NIVOI:
        if pp >= granica:
            return ime
    return 'nagoveštaj'


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


def izbor_utakmice(kand):
    """kand: dict(igr, s, strana, pp, ev, k) za jednu utakmicu (k = kvota). Vraća 4 do 6 predloga, najviše jedan po igraču,
    sa poljima nivo i rang. Po igraču se uzima stavka i strana sa najvećim viškom verovatnoće iznad praga."""
    po_stavci = {}
    for c in kand:
        if c['k'] < KVOTA_MIN:
            continue
        kl = (c['igr'], c['s'], c['strana'])
        if kl not in po_stavci or c['ev'] > po_stavci[kl]['ev']:      # najbolja cena za istu stavku i stranu
            po_stavci[kl] = c
    po_igracu = {}
    for c in po_stavci.values():
        c['sk'] = c['pp'] - PRAG[c['strana']]
        if c['igr'] not in po_igracu or (c['sk'], c['ev']) > (po_igracu[c['igr']]['sk'], po_igracu[c['igr']]['ev']):
            po_igracu[c['igr']] = c
    L = sorted(po_igracu.values(), key=lambda c: (-c['sk'], -c['ev']))
    ok = [c for c in L if c['sk'] >= 0]
    out = [c for c in ok if c['strana'] == 'o'][:PLUS_MIN]
    for c in ok:
        if len(out) >= MAX_UT:
            break
        if c not in out:
            out.append(c)
    slabi = []
    for c in L:
        if len(out) + len(slabi) >= MIN_UT:
            break
        if c not in out:
            slabi.append(c)
    rez = []
    for c in sorted(out, key=lambda c: -c['pp']):
        rez.append(dict(c, nivo=nivo(c['pp'])))
    for c in slabi:
        rez.append(dict(c, nivo=nivo(c['pp'], slab=True)))
    for r, c in enumerate(rez, 1):
        c['rang'] = r
        c.pop('sk', None)
    return rez


def predlozi_unazad(w, R, g_od):
    """R: granice iz provere; g_od(r) -> šifra utakmice. Isto pravilo po utakmici."""
    po_g = {}
    for r in R:
        g = g_od(r)
        if g is None:
            continue
        p = preko(w, r['s'], r['pm'], r['tr'])
        for strana, pp, k, prosao in (('o', p, r['o'], r['preko'] == 1), ('u', 1 - p, r['u'], r['preko'] == 0)):
            po_g.setdefault(g, []).append(dict(igr=r['k'], s=r['s'], strana=strana, pp=pp, ev=pp * k - 1, k=k,
                                                prosao=prosao, kolo=r['kolo']))
    out = []
    for g, C in po_g.items():
        out += izbor_utakmice(C)
    return out, len(po_g)


def main():
    R = ucitaj(os.path.join(PROCENE, 'provera', 'granice.json'))
    w_sve = podesi(R)
    tr = [r for r in R if r['kolo'] <= 6]
    te = [r for r in R if r['kolo'] >= 7]
    w_tr = podesi(tr)
    from model import Baza
    B = Baza()
    g_idx = {(x['k'], x['dan']): x['g'] for x in B.rows}
    g_od = lambda r: g_idx.get((r['k'], r['dan']))

    def zbir(X, kljuc):
        grupe = {}
        for x in X:
            a = grupe.setdefault(kljuc(x), dict(n=0, prosao=0, dobit=0.0, pp=0.0))
            a['n'] += 1; a['prosao'] += x['prosao']; a['dobit'] += (x['k'] - 1) if x['prosao'] else -1; a['pp'] += x['pp']
        return {k: dict(n=v['n'], prosao=v['prosao'], dobit=round(v['dobit'], 2), pp=round(v['pp'] / v['n'], 3))
                for k, v in sorted(grupe.items())}

    test = {}
    for ime, X in (('kola_7_9', te), ('kola_4_6', tr)):
        P, n_ut = predlozi_unazad(w_tr, X, g_od)
        test[ime] = dict(utakmica=n_ut, predloga=len(P),
                         ukupno=zbir(P, lambda x: 'sve')['sve'],
                         po_strani=zbir(P, lambda x: 'plus' if x['strana'] == 'o' else 'minus'),
                         po_nivou=zbir(P, lambda x: x['nivo']),
                         po_kolu=zbir(P, lambda x: x['kolo']))
    test['opis'] = ('koeficijenti spajanja iz kola 4–6; kola 7–9 su van podešavanja, kola 4–6 su u periodu podešavanja. '
                    'Admiral i MaxBet, jedna kladionica po danu, samo glavne granice')
    ll = lambda p, y: -(y * math.log(p) + (1 - y) * math.log(1 - p))
    test.update(ll_spojeno=round(sum(ll(preko(w_tr, r['s'], r['pm'], r['tr']), r['preko']) for r in te) / len(te), 4),
                ll_kvote=round(sum(ll(min(max(r['tr'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4),
                ll_model=round(sum(ll(min(max(r['pm'], 1e-4), 1 - 1e-4), r['preko']) for r in te) / len(te), 4))
    out = dict(w=w_sve, w_kola_4_6=w_tr, n_granica=len(R), pravilo=dict(kvota_min=KVOTA_MIN, prag_minus=PRAG['u'], prag_plus=PRAG['o'], min_ut=MIN_UT, max_ut=MAX_UT, plus_min=PLUS_MIN,
                                                               nivoi=[[g, n] for g, n in NIVOI]), test=test)
    sacuvaj(os.path.join(PROCENE, 'spajanje.json'), out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
