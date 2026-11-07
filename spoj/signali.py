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
