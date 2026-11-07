"""Minus-model u Pythonu: prepis funkcije estimate() iz minusi/aplikacija/app.js (Generator), da bi ga koristile
i procene i provere. Sve se računa samo iz utakmica PRE dana utakmice.

Razlike u odnosu na aplikaciju (namerno, da bi bilo ponovljivo unazad):
  - nema dodatka za odsutne saigrače (b = 1) i nema kvota za ukupne poene tima (tempo iz proseka timova);
  - polazna procena (prošla sezona) je procene/podaci/e2025_igraci.json, a ne karijera iz stanja aplikacije.
Provera vernosti: na kolima 4-7 najbolja četvrtina po ovoj proceni prolazi 68% (aplikacija beleži 69%).

Glavni izlaz je `msig`: deo minus-procene koji NE dolazi iz kvota (logit). Veći = model jače vidi ISPOD.
Prag slaganja za procene: MSIG_PRAG (medijana na svim granicama kola 4-10).

  from minus_model import MinusModel
  mm = MinusModel(B)          # B = procene Baza (model.Baza)
  r = mm.procena(k, dan, tim, protivnik, 'P', 12.5, fer_ispod)
"""
import collections, math, statistics as stt

MSIG_PRAG = 0.35
EST = dict(c=0.16, kf=0.5, A=0.12, S=0.08, P10=0.12)
ADJ = dict(of=1.5, pace=1.5, close=0.2, hot=0.15, dogB=0.1, taA=1.0)
IX = {'P': 0, 'S': 1, 'A': 2}


def lgt(p):
    p = max(0.02, min(0.98, p))
    return math.log(p / (1 - p))


def _ncdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _pois_cdf(k, m):
    s, t = 0.0, math.exp(-m)
    for i in range(int(k) + 1):
        if i > 0:
            t *= m / i
        s += t
    return s


def model_under(s, l, avg):
    """Ista raspodela kao modelUnder() u aplikaciji."""
    if avg is None:
        return None
    if s == 'P':
        return _ncdf((l - avg) / (0.35 * avg + 2.5))
    return _pois_cdf(math.floor(l), max(avg, 0.1))


class MinusModel:
    def __init__(self, B):
        self.B = B
        self._ctx = {}

    def ctx2(self, dan):
        """Kontekst kao baza/skripte/ctx2.py, ali samo iz utakmica pre dana."""
        if dan in self._ctx:
            return self._ctx[dan]
        R = [r for r in self.B.rows if r['dan'] < dan]
        al = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0])))
        for r in R:
            if r['pos'] not in ('G', 'F', 'C'):
                continue
            a = al[r['opp']][r['g']][r['pos']]; a[0] += r['P']; a[1] += r['S']; a[2] += r['A']
        lg = {}
        for pos in 'GFC':
            vals = [al[t][g][pos] for t in al for g in al[t]]
            lg[pos] = [stt.mean(v[i] for v in vals) if vals else 1 for i in range(3)]
        of = {}
        for t, gs in al.items():
            n = len(gs); of[t] = {}
            for pos in 'GFC':
                of[t][pos] = [1 + ((stt.mean(gs[g][pos][i] for g in gs) / lg[pos][i]) - 1) * n / (n + 6) if lg[pos][i] else 1
                              for i in range(3)]
        tg = collections.defaultdict(dict)
        for r in R:
            d = tg[r['team']].setdefault(r['g'], {'pts': 0, 'opp': r['opp']}); d['pts'] += r['P']
        tm = {}
        for t, gs in tg.items():
            pf = [d['pts'] for d in gs.values()]
            pa = [tg[d['opp']][g]['pts'] for g, d in gs.items() if g in tg[d['opp']]]
            tm[t] = [stt.mean(pf), stt.mean(pa) if pa else stt.mean(pf), len(pf)]
        lgp = stt.mean(v[0] for v in tm.values()) if tm else 85
        og = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))
        for r in R:
            a = og[r['opp']][r['g']]; a[0] += r['P']; a[1] += r['S']; a[2] += r['A']
        lgo = [stt.mean(v[i] for t in og for v in og[t].values()) for i in range(3)] if og else [1, 1, 1]
        ta = {t: [1 + ((stt.mean(v[i] for v in gs.values()) / lgo[i]) - 1) * len(gs) / (len(gs) + 6) for i in range(3)]
              for t, gs in og.items()}
        self._ctx[dan] = dict(of=of, tm=tm, lgp=lgp, ta=ta)
        return self._ctx[dan]

    def procena(self, k, dan, team, opp, s, l, fair_u):
        """Minus-procena za igrača k (ključ iz baze) na dan, stavka s, granica l; fair_u = verovatnoća ispod iz kvota."""
        B = self.B
        g = [r for r in B.byk.get(k, []) if r['dan'] < dan and r['min'] > 0]
        pr = B.prosla.get(k)
        if not g and not pr:
            return None
        cur = pp = None
        if g:
            n = len(g)
            cur = dict(v=sum(r[s] for r in g) / n, g=n, min=sum(r['min'] for r in g) / n)
        if pr and pr.get('n') and pr.get('min'):
            pp = dict(g=pr['n'], min=pr['min'] / pr['n'], v=pr[s] / pr['n'])
        if cur and pp:
            wcur = cur['g'] / (cur['g'] + 4)
            rate = wcur * (cur['v'] / cur['min']) + (1 - wcur) * (pp['v'] / pp['min'])
            w2 = cur['g'] / (cur['g'] + 2)
            minP = w2 * cur['min'] + (1 - w2) * pp['min']
        elif cur:
            rate = cur['v'] / cur['min']; minP = cur['min']
        elif pp:
            rate = pp['v'] / pp['min']; minP = pp['min']
        else:
            return None
        v = rate * minP
        nEff = min(pp['g'] if pp else 0, 60) + (cur['g'] * 3 if cur else 0)
        z = EST['c'] + EST['kf'] * lgt(fair_u)
        if s == 'A':
            z += EST['A']
        elif s == 'S':
            z += EST['S']
        elif l >= 10.5:
            z += EST['P10']
        z += -0.25 if minP < 12 else -0.08 if minP < 17 else 0 if minP < 21 else 0.15 if minP < 25 else 0.12
        mins = [r['min'] for r in g][-10:]
        cv = None
        if len(mins) >= 3:
            mm = stt.mean(mins)
            cv = stt.pstdev(mins) / mm if mm > 0 else None
            if cv is not None:
                z -= 0.4 * max(0, min(1, (cv - 0.2) / 0.15))
        C = self.ctx2(dan)
        ix = IX[s]
        pos = collections.Counter(r['pos'] for r in g).most_common(1)[0][0] if g else ''
        st = sum(r['st'] for r in g) / len(g) if g else 0
        dz = 0.0
        if opp in C['of'] and pos in C['of'][opp]:
            ofv = max(0.8, min(1.2, C['of'][opp][pos][ix])); dz += -ADJ['of'] * (ofv - 1)
        tm = C['tm']
        if team in tm and opp in tm:
            pace = max(0.85, min(1.15, ((tm[team][0] + tm[opp][1]) / 2) / C['lgp'])); dz += -ADJ['pace'] * (pace - 1)
            spread = (tm[team][0] - tm[team][1]) - (tm[opp][0] - tm[opp][1])
            if abs(spread) <= 5:
                dz += ADJ['close']
            if spread < -5 and st < 0.5:
                dz -= ADJ['dogB']
        if len(g) >= 3:
            tot_m = sum(r['min'] for r in g); l3 = g[-3:]; m3 = sum(r['min'] for r in l3)
            rr = sum(r[s] for r in g) / tot_m if tot_m else 0
            r3 = sum(r[s] for r in l3) / m3 if m3 else 0
            if rr > 0 and r3 / rr > 1.3:
                dz -= ADJ['hot']
        if s == 'A' and opp in C['ta']:
            taA = max(0.75, min(1.25, C['ta'][opp][2])); dz -= ADJ['taA'] * (taA - 1)
        z += dz
        mpR = model_under(s, l, v)
        if mpR is not None and nEff > 0:
            z += 0.25 * nEff / (nEff + 20) * (lgt(mpR) - lgt(fair_u))
        p = max(0.3, min(0.8, 1 / (1 + math.exp(-z))))
        return dict(msig=round(z - EST['kf'] * lgt(fair_u), 4), mpu=round(p, 4), mmean=round(v, 2), mminP=round(minP, 1),
                    mcv=round(cv, 3) if cv is not None else None)
