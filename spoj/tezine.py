"""Uči težine spoja iz svih Admiral granica sa ishodom (posle svakog kola):
  python3 spoj/provera.py && python3 spoj/analiza/prep.py && python3 spoj/tezine.py
Model: logit(ispod) = logit(tržište) + b + Σ w·osobina. Nagibi se uče na svim kolima (od 4.), slobodni član b samo na
poslednja 4 kola, jer se opšta prednost minusa menja. Izlaz: spoj/tezine.json (koristi signali.spoj2)."""
import json, math, os, sys, statistics as st, collections, datetime
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signali
from signali import lgt, osobine
F = [x for x in json.load(open(os.path.join(signali.KOREN, 'spoj', 'analiza', 'F.json'))) if x['izvor'] == 'admiral']
FE = ['pu', 'ms', 'mm', 'zl', 'pmid', 'mt', 'hot', 'tempo', 'minsd']
for x in F:
    x['X'] = osobine(x['pm'], x['tr'], x['msig'], x['missmin'], x['zline'], x['s'], x['l'], x); x['Lq'] = lgt(1 - x['tr']); x['y'] = 1 - x['preko']
sg = lambda z: 1 / (1 + math.exp(-z))


def uci(R, kola_b):
    mean = {f: st.mean(x['X'][f] for x in R) for f in FE}; sd = {f: st.pstdev(x['X'][f] for x in R) or 1 for f in FE}
    X = np.array([[1] + [(x['X'][f] - mean[f]) / sd[f] for f in FE] for x in R]); y = np.array([x['y'] for x in R], float); off = np.array([x['Lq'] for x in R])
    w = np.zeros(X.shape[1])
    for _ in range(80):
        p = 1 / (1 + np.exp(-(off + X @ w))); g = X.T @ (p - y) + 2.0 * np.r_[0, w[1:]]
        H = (X.T * (p * (1 - p))) @ X + 2.0 * np.diag(np.r_[0, np.ones(len(w) - 1)]); w -= np.linalg.solve(H, g)
    W = dict(zip(FE, map(float, w[1:])))
    Rb = [x for x in R if x['kolo'] in kola_b]; b = float(w[0])
    for _ in range(50):       # slobodni član samo na poslednjim kolima
        ps = [sg(x['Lq'] + b + sum(W[f] * (x['X'][f] - mean[f]) / sd[f] for f in FE)) for x in Rb]
        b += (sum(x['y'] for x in Rb) - sum(ps)) / max(1e-6, sum(p * (1 - p) for p in ps))
    return dict(osobine=FE, mean=mean, sd=sd, w=W, b=b)


def p_ispod(T, x):
    return sg(x['Lq'] + T['b'] + sum(T['w'][f] * (x['X'][f] - T['mean'][f]) / T['sd'][f] for f in FE))


kola = sorted({x['kolo'] for x in F})
# provera unapred: za svako kolo od 8. uči na ranijim, predviđa to kolo
T8 = []
for k in [k for k in kola if k >= 8]:
    tr = [x for x in F if x['kolo'] < k]; T = uci(tr, set(sorted({x['kolo'] for x in tr})[-4:]))
    for x in F:
        if x['kolo'] == k:
            x['p2'] = p_ispod(T, x); x['p1'] = sg(x['Lq'] + 0.15 * (lgt(x['mpu']) - x['Lq'] - 0.16) + 0.30 * x['X']['pu']); T8.append(x)
byd = collections.defaultdict(list)
for x in T8:
    if x['u'] >= 1.6:
        byd[x['dan']].append(x)
def vrh(key, a, b):
    S = []
    for L in byd.values():
        L = sorted(L, key=lambda x: -x[key] * x['u']); S += L[int(len(L) * a):int(len(L) * b)]
    return f"{sum(x['y'] for x in S) / len(S):.1%} (n={len(S)}, povraćaj {sum((x['u'] - 1) if x['y'] else -1 for x in S) / len(S):+.1%})"
print('Provera unapred, kola 8+ (kvota ≥ 1,60), izbor po vrednosti u danu:')
for nm, key in (('stari spoj (fiksne težine)', 'p1'), ('novi spoj (naučene težine + novi parametri)', 'p2')):
    print(f"  {nm}: najboljih 25% {vrh(key, 0, .25)} | 25-40% {vrh(key, .25, .40)} | 40-60% {vrh(key, .40, .60)} | donjih 40% {vrh(key, .60, 1)}")
T = uci(F, set(kola[-4:])); T.update(at=datetime.datetime.now().isoformat(timespec='minutes'), n=len(F), kola=[kola[0], kola[-1]])
json.dump(T, open(signali.TEZINE_PUT, 'w'), ensure_ascii=False, indent=1)
print('težine (po standardnoj devijaciji; + znači više ispod):', {f: round(v, 3) for f, v in T['w'].items()}, '| slobodni član', round(T['b'], 3), '| granica', len(F))
