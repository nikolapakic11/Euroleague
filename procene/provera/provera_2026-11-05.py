"""Provera tri ideje posle 5.11.2026 (kolo 10, prve dve utakmice 2/5):
  1. obavezni PLUS predlozi (PLUS_MIN) i dopuna do 6
  2. PLUS na poene za igrače sa malo minuta i nulom u poslednjih 9
  3. jače vezivanje modela za prosek sezone (mu' = a·mu + (1−a)·prosek), svuda ili samo kad je model ispod proseka

  python3 procene/provera/provera_2026-11-05.py     (posle provera.py)

Walk-forward: za kolo k koeficijenti spajanja se podešavaju samo na ranijim kolima, pa se primenjuje izbor po utakmici.
Granice iz procene/provera/granice.json (glavne granice, sve kladionice). Ništa se ne menja u pravilima.
"""
import collections, json, math, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte'))
os.chdir(KOREN)
import model, spajanje as S
from model import Baza, verovatnoca_preko

R = json.load(open('procene/provera/granice.json'))
model.ucitaj_parametre()
B = Baza()
g_idx = {(x['k'], x['dan']): x['g'] for x in B.rows}

# istorija pre dana: prosek stavke, prosek minuta, nula u poslednjih 9 (poeni)
for r in R:
    h = [x for x in B.byk.get(r['k'], []) if x['dan'] < r['dan']]
    r['n_pre'] = len(h)
    r['avg'] = st.mean(x[r['s']] for x in h) if h else None
    r['min_avg'] = st.mean(x['min'] for x in h) if h else None
    r['nula9'] = any(x['P'] == 0 for x in h[-9:])
    r['g'] = g_idx.get((r['k'], r['dan']))


def pm_skupljen(r, a):
    if r['avg'] is None or r['n_pre'] < 3 or a == 1:
        return r['pm']
    if isinstance(a, str):          # 'dole_x': skupljanje samo kad je model ispod proseka
        a = float(a.split('_')[1])
        if r['mu'] >= r['avg']:
            return r['pm']
    mu2 = a * r['mu'] + (1 - a) * r['avg']
    mu2 = max(mu2, 0.05)
    var2 = r['var'] * mu2 / r['mu'] if r['mu'] > 0 else r['var']
    var2 = max(var2, mu2 * 1.0001)
    return verovatnoca_preko(r['s'], mu2, var2, r['l'])


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def izbor(C, plus_min, min_ut, filter_poeni):
    stari = (S.PLUS_MIN, S.MIN_UT)
    S.PLUS_MIN, S.MIN_UT = plus_min, min_ut
    if filter_poeni:
        C = [c for c in C if not (c['strana'] == 'o' and c['s'] == 'P' and c['rizik'])]
    try:
        return S.izbor_utakmice(C)
    finally:
        S.PLUS_MIN, S.MIN_UT = stari


def kandidati(w, X, pmk):
    po_g = collections.defaultdict(list)
    for r in X:
        if r['g'] is None:
            continue
        p = S.preko(w, r['s'], r[pmk], r['tr'])
        rizik = (r['min_avg'] or 0) < 20 and r['nula9']
        for strana, pp, k, ok in (('o', p, r['o'], r['preko'] == 1), ('u', 1 - p, r['u'], r['preko'] == 0)):
            po_g[r['g']].append(dict(igr=r['k'], s=r['s'], strana=strana, pp=pp, ev=pp * k - 1, k=k, prosao=ok,
                                     kolo=r['kolo'], tim=r.get('tk'), rizik=rizik))
    return po_g


def zbir(P):
    n = len(P)
    if not n:
        return dict(n=0)
    pr = sum(x['prosao'] for x in P)
    dob = sum((x['k'] - 1) if x['prosao'] else -1 for x in P)
    return dict(n=n, prosao=pr, pogodak=round(pr / n, 3), dobit=round(dob, 2), povracaj=round(dob / n, 3),
                kvota=round(st.mean(x['k'] for x in P), 2))


VARIJANTE = [
    ('sada: bar 2 PLUS, najmanje 6', dict(plus_min=2, min_ut=6, filter_poeni=False)),
    ('bar 1 PLUS, najmanje 6', dict(plus_min=1, min_ut=6, filter_poeni=False)),
    ('bez obaveznog PLUS, najmanje 6', dict(plus_min=0, min_ut=6, filter_poeni=False)),
    ('bar 2 PLUS, bez dopune do 6', dict(plus_min=2, min_ut=0, filter_poeni=False)),
    ('bez obaveznog PLUS, bez dopune', dict(plus_min=0, min_ut=0, filter_poeni=False)),
    ('sada + filter poena (malo minuta, nula)', dict(plus_min=2, min_ut=6, filter_poeni=True)),
]
ALFE = [1.0, 0.85, 0.7, 0.5, 'dole_0.7', 'dole_0.5']

kola = sorted({r['kolo'] for r in R})
rez = {}
ll_tab = {}
for a in ALFE:
    pmk = f'pm_{a}'
    for r in R:
        r[pmk] = pm_skupljen(r, a)
    sve = {ime: [] for ime, _ in VARIJANTE}
    lls = dict(model=[], spojeno=[], kvote=[])
    for k in kola:
        ranije = [r for r in R if r['kolo'] < k]
        if len(ranije) < 250:
            continue
        ranije_x = [dict(r, pm=r[pmk]) for r in ranije]
        w = S.podesi(ranije_x)
        X = [r for r in R if r['kolo'] == k]
        for r in X:
            lls['model'].append(ll(r[pmk], r['preko']))
            lls['spojeno'].append(ll(S.preko(w, r['s'], r[pmk], r['tr']), r['preko']))
            lls['kvote'].append(ll(r['tr'], r['preko']))
        po_g = kandidati(w, X, pmk)
        for ime, par in VARIJANTE:
            for g, C in po_g.items():
                sve[ime] += izbor([dict(c) for c in C], **par)
    ll_tab[a] = {k: round(st.mean(v), 4) for k, v in lls.items()} | dict(n=len(lls['model']))
    rez[a] = {ime: dict(ukupno=zbir(P),
                        plus=zbir([x for x in P if x['strana'] == 'o']),
                        minus=zbir([x for x in P if x['strana'] == 'u']),
                        po_kolu={k: zbir([x for x in P if x['kolo'] == k]) for k in kola if any(x['kolo'] == k for x in P)})
              for ime, P in sve.items()}

# odstupanje modela od proseka: gde završi stvarni učinak (sve granice, model bez skupljanja)
odst = []
for lo, hi in ((0, 0.85), (0.85, 1.15), (1.15, 1.3), (1.3, 99)):
    G = [r for r in R if r['avg'] and r['n_pre'] >= 3 and lo <= r['mu'] / r['avg'] < hi]
    if G:
        odst.append(dict(raspon=f'{lo}–{hi}', n=len(G), model=round(st.mean(r['mu'] for r in G), 2),
                         prosek=round(st.mean(r['avg'] for r in G), 2), stvarno=round(st.mean(r['ishod'] for r in G), 2)))

out = dict(ll=ll_tab, izbor=rez, odstupanje=odst)
json.dump(out, open('procene/provera/provera_2026-11-05.json', 'w'), ensure_ascii=False, indent=1)
for a in ALFE:
    print(f'\n== a={a}  log gubitak', ll_tab[a])
    for ime, v in rez[a].items():
        u, p, m = v['ukupno'], v['plus'], v['minus']
        print(f"  {ime:42} {u['n']:4} {u['pogodak']:.3f} povr {u['povracaj']:+.3f} | PLUS {p.get('n',0):3} {p.get('pogodak',0):.3f} {p.get('povracaj',0):+.3f} | MINUS {m.get('n',0):3} {m.get('pogodak',0):.3f} {m.get('povracaj',0):+.3f}")
print('\nodstupanje', odst)
