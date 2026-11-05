"""Senka: predlozi po varijanti „skupljanje samo nadole“, uporedo sa pravim, bez prikaza (odluka 5.11.2026).

  python3 procene/skripte/senka.py --kolo 11      (posle tabla.py; poziva ga dan.py)
  python3 procene/skripte/senka.py --pregled      (zbir svih kola sa ishodima)

Varijanta (procene/provera/provera_2026-11-05.md): kad je očekivanje modela ispod proseka igrača u sezoni,
  mu' = 0,7·mu + 0,3·prosek (rasipanje srazmerno), pa spajanje sa kvotama podešeno na istoj varijanti
(procene/provera/granice.json). Kad je model iznad proseka, ništa se ne menja.
Za svaku utakmicu iz table istog trenutka bira predloge i po važećem pravilu i po varijanti (ista isključenja:
ne igra, upitan, tim bez MINUS-a, nova pojačanja), da bi poređenje bilo pošteno. Utakmica koja je počela se više
ne menja (ostaje stanje pred početak). Ishodi iz zapisnika. Izlaz: procene/senka/kolo<N>.json.
Ništa od ovoga ne ide na stranicu i ne menja prave predloge.
"""
import argparse, glob, json, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(__file__))
import spajanje as S
from model import Baza, verovatnoca_preko
from zajedno import PROCENE, ucitaj, sacuvaj

A = 0.7
MIN_KOLA = 3          # posle ovoliko kola sa ishodima dan.py podseća da se odluči


def pm_varijanta(s, mu, var, pros, l):
    if pros is None or mu >= pros:
        return verovatnoca_preko(s, mu, var, l)
    mu2 = max(A * mu + (1 - A) * pros, 0.05)
    var2 = max(var * mu2 / mu if mu > 0 else var, mu2 * 1.0001)
    return verovatnoca_preko(s, mu2, var2, l)


def w_varijanta(B):
    R = ucitaj(os.path.join(PROCENE, 'provera', 'granice.json'))
    X = []
    for r in R:
        h = [x[r['s']] for x in B.byk.get(r['k'], []) if x['dan'] < r['dan']]
        pros = st.mean(h) if len(h) >= 3 else None
        X.append(dict(r, pm=pm_varijanta(r['s'], r['mu'], r['var'], pros, r['l'])))
    return S.podesi(X)


def kandidati(u, varijanta, w):
    kand = []
    for st_i in u['strane']:
        bez_minusa = bool(st_i.get('nedostaju'))
        for i in st_i['igraci']:
            if i['ne_igra'] or i.get('upitan') or i['odsutan'] > 0 or i['n'] < 3:
                continue
            for s in 'PSA':
                x = i['s'][s]
                for z in x['linije']:
                    if not z.get('m', 1):
                        continue
                    if varijanta:
                        pm = pm_varijanta(s, x['mu'], x['var'], x.get('pros') if i['n'] >= 3 else None, z['l'])
                        ps = S.preko(w, s, pm, z.get('trk', z['tr']))
                    else:
                        ps = z.get('ps', z['pc'])
                    for strana, pp, kv in (('o', ps, z['o']), ('u', 1 - ps, z['u'])):
                        if strana == 'u' and bez_minusa:
                            continue
                        if strana == 'o' and i.get('novi_saigrac'):
                            continue
                        kand.append(dict(igr=i['k'], ime=i['ime'], tim=st_i['tim'], s=s, strana=strana, pp=pp,
                                         ev=pp * kv - 1, k=kv, l=z['l'], kl=z['kl']))
    return kand


def ishodi(dn, B):
    po_g = {}
    for k, G in B.byk.items():
        for r in G:
            po_g[(r['g'], k)] = r
    for g, X in dn['utakmice'].items():
        for var in ('sada', 'senka'):
            for p in X[var]:
                r = po_g.get((int(g), p['igr']))
                if r is not None:
                    p['ishod'] = r[p['s']]
                    p['prosao'] = (r[p['s']] > p['l']) if p['strana'] == 'o' else (r[p['s']] < p['l'])


def zbir(P):
    P = [p for p in P if 'prosao' in p]
    if not P:
        return None
    n, pr = len(P), sum(p['prosao'] for p in P)
    dob = sum((p['k'] - 1) if p['prosao'] else -1 for p in P)
    return dict(n=n, prosao=pr, dobit=round(dob, 2))


def pregled():
    tot = {'sada': [], 'senka': []}
    kola = 0
    for f in sorted(glob.glob(os.path.join(PROCENE, 'senka', 'kolo*.json'))):
        dn = ucitaj(f)
        ima = False
        for X in dn['utakmice'].values():
            for v in tot:
                tot[v] += X[v]
                ima = ima or any('prosao' in p for p in X[v])
        kola += ima
    out = {v: zbir(P) for v, P in tot.items()}
    return kola, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    ap.add_argument('--pregled', action='store_true')
    a = ap.parse_args()
    if a.pregled or not a.kolo:
        kola, out = pregled()
        print(f'senka: kola sa ishodima {kola};', ' | '.join(
            f"{v}: {o['prosao']}/{o['n']} dobit {o['dobit']:+.2f}" if o else f'{v}: još nema' for v, o in out.items()))
        return
    B = Baza()
    T = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
    p = os.path.join(PROCENE, 'senka', f'kolo{a.kolo}.json')
    dn = ucitaj(p) if os.path.exists(p) else {'kolo': a.kolo, 'opis': f'skupljanje nadole, a={A}', 'utakmice': {}}
    w = w_varijanta(B)
    dn['w'] = w
    novo = 0
    for u in T['utakmice']:
        if u.get('pocela') and str(u['g']) in dn['utakmice']:
            continue
        sada = S.izbor_utakmice(kandidati(u, False, w))
        senka = S.izbor_utakmice(kandidati(u, True, w))
        polja = ('ime', 'igr', 'tim', 's', 'strana', 'l', 'kl', 'k', 'pp', 'rang')
        if not sada and not senka:
            continue
        dn['utakmice'][str(u['g'])] = dict(dan=u['dan'], upisano=T['napravljeno'],
                                           sada=[{k: c[k] for k in polja} for c in sada],
                                           senka=[{k: c[k] for k in polja} for c in senka])
        novo += 1
    ishodi(dn, B)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    sacuvaj(p, dn)
    razlika = sum(len({(c['igr'], c['s'], c['strana']) for c in X['senka']} - {(c['igr'], c['s'], c['strana']) for c in X['sada']})
                  for X in dn['utakmice'].values())
    print(f'senka kolo {a.kolo}: utakmica {len(dn["utakmice"])} (osveženo {novo}), predloga koji se razlikuju {razlika}')


if __name__ == '__main__':
    main()
