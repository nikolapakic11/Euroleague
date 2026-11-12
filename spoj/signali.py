"""Zajednički signali za oba projekta: model procena (verovatnoća za preko) i minus-model (msig).

  import sys; sys.path.insert(0, '<repo>/spoj'); import signali
  S = signali.Signali()                       # učita bazu (baza/rows.json + procene/podaci/dopuna.json) i parametre
  pm = S.procene_preko(k, dan, tim, prot, 'P', 12.5)
  m  = S.minus(k, dan, tim, prot, 'P', 12.5, fer_ispod)     # dict sa msig, mpu, ...
  k, tk = S.nadji('Lonnie Walker IV', 'Besiktas')
"""
import math, os, sys
KOREN = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import model as _pm                      # procene/skripte/model.py
from minus_model import MinusModel, MSIG_PRAG, lgt

# težine spoja (provera: spoj/provera/izvestaj.md)
W_MINUS_ISPOD = 0.15     # minus-model u verovatnoći za tikete (izbor.py, kao do sada)
W_PROCENE_ISPOD = 0.30   # model procena u verovatnoći za tikete (novo, 7.11.2026)


class Signali:
    def __init__(self, B=None):
        _pm.ucitaj_parametre()
        self.B = B or _pm.Baza()
        self.M = MinusModel(self.B)

    def nadji(self, ime, t=None, tk=None):
        return self.B.nadji_u_utakmici(ime, t, tk)

    def procene_preko(self, k, dan, tim, prot, s, l):
        e = self.B.procena(k, dan, tim, prot)
        if not e or e['n'] < 2:
            return None
        sx = e['s'][s]
        return _pm.verovatnoca_preko(s, sx['mu'], sx['var'], l)

    def minus(self, k, dan, tim, prot, s, l, fer_ispod):
        return self.M.procena(k, dan, tim, prot, s, l, fer_ispod)


def spoj_ispod(fer_ispod, p_app=None, pm_preko=None):
    """Verovatnoća ISPOD za tikete: tržište + 0,15·(minus aplikacije − tržište − 0,16) + 0,30·(tržište − procene)."""
    z = lgt(fer_ispod)
    if p_app is not None:
        z += W_MINUS_ISPOD * (lgt(p_app) - lgt(fer_ispod) - 0.16)
    if pm_preko is not None:
        z += W_PROCENE_ISPOD * (lgt(1 - pm_preko) - lgt(fer_ispod))
    return 1 / (1 + math.exp(-z))


# ---------------------------------------------------------------------------------------------------------------
# Novi parametri (od 12.11.2026; analiza spoj/analiza/IZVESTAJ_2026-11-12.md): izostanci u timu, granica prema
# proseku igrača, kazna za poene 7,5-10,5; težine se uče iz podataka (spoj/tezine.py -> spoj/tezine.json).
import collections as _c, json as _json, statistics as _st

TEZINE_PUT = os.path.join(KOREN, 'spoj', 'tezine.json')
IZOSTANCI_PRAG = 35          # minuta rotacije koji fale: iznad ovoga minusi na taj tim ne prolaze (49%)


def _tim_redovi(S, tim, dan):
    return [r for r in S.B.rows if r['team'] == tim and r['dan'] < dan and r['min'] > 0]


def rotacija(S, tim, dan):
    """Igrači rotacije pre dana: bar 3 utakmice i prosek bar 10 minuta -> {k: prosečni minuti}."""
    pre = _c.defaultdict(list)
    for r in _tim_redovi(S, tim, dan):
        pre[r['k']].append(r['min'])
    return {k: sum(m) / len(m) for k, m in pre.items() if len(m) >= 3 and sum(m) / len(m) >= 10}


def izostanci(S, tim, dan, pov=None):
    """Minuti rotacije koji fale timu -> {k: minuti}. pov = {k: {stanje: van|upitan|igra, tekst}} (izveštaj o povredama).
    Bez izveštaja: igrač rotacije koji nije igrao poslednje dve utakmice tima računa se kao odsutan."""
    pov = pov or {}
    rot = rotacija(S, tim, dan)
    dani = sorted({r['dan'] for r in S.B.rows if r['team'] == tim and r['dan'] < dan})[-2:]
    skoro = {r['k'] for r in S.B.rows if r['team'] == tim and r['dan'] in dani and r['min'] > 0}
    out = {}
    for k, m in rot.items():
        x = pov.get(k) or {}
        st, tx = x.get('stanje'), x.get('tekst', '') or ''
        if st == 'van':
            w = 1.0
        elif st == 'igra':
            w = 0.0
        elif st == 'upitan':
            w = 1.0 if k not in skoro else (0.0 if "coach's decision" in tx else 0.5)
        else:
            w = 0.0 if k in skoro else 1.0
        if w:
            out[k] = round(w * m, 1)
    return out


def rang_u_timu(S, k, tim, dan, s):
    a = _c.defaultdict(list)
    for r in _tim_redovi(S, tim, dan):
        a[r['k']].append(r[s])
    m = {p: sum(v) / len(v) for p, v in a.items() if len(v) >= 3}
    moj = m.get(k)
    if moj is None:
        v = a.get(k)
        if not v:
            return None
        moj = sum(v) / len(v)
    return 1 + sum(1 for p, x in m.items() if x > moj and p != k)


def zline(S, k, dan, s, l):
    """(granica - prosek igrača) / rasipanje; negativno = granica ispod proseka (tada ispod prolazi češće)."""
    v = [r[s] for r in S.B.byk.get(k, []) if r['dan'] < dan and r['min'] > 0]
    if len(v) < 2:
        return None
    avg = sum(v) / len(v)
    sd = _st.pstdev(v) if len(v) > 2 else max(1, avg ** .5)
    return (l - avg) / max(sd, 0.8)


def osobine(pm_preko, tr_preko, msig, missmin, zl, s, l):
    """Osobine za naučeni spoj (isto u učenju i u primeni). Nedostajuća vrednost -> None (uzima se prosek)."""
    return dict(pu=(lgt(1 - pm_preko) - lgt(1 - tr_preko)) if pm_preko is not None else None,
                ms=msig,
                mm=(min(missmin, 60) / 20.0) if missmin is not None else None,
                zl=max(-2.0, min(2.0, zl)) if zl is not None else None,
                pmid=1.0 if (s == 'P' and 6.5 < l <= 10.5) else 0.0)


_TEZ = None


def tezine():
    global _TEZ
    if _TEZ is None:
        _TEZ = _json.load(open(TEZINE_PUT))
    return _TEZ


def spoj2(fer_ispod, pm_preko, msig, missmin, zl, s, l):
    """Verovatnoća ISPOD po naučenim težinama: tržište + slobodni član (poslednja 4 kola) + oba modela + novi parametri."""
    T = tezine()
    X = osobine(pm_preko, 1 - fer_ispod, msig, missmin, zl, s, l)
    z = lgt(fer_ispod) + T['b']
    for f in T['osobine']:
        x = X.get(f)
        if x is None:
            continue
        z += T['w'][f] * (x - T['mean'][f]) / T['sd'][f]
    return 1 / (1 + math.exp(-z))
