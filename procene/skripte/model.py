"""Model raspona za igrače Evrolige: poeni (P), skokovi (S), asistencije (A).

Za igrača, stavku i utakmicu daje očekivani učinak, raspodelu (negativna binomna),
raspon (10/25/50/75/90. percentil) i verovatnoću za preko i ispod bilo koje granice.

Sve se računa samo iz utakmica pre dana utakmice (bez curenja budućnosti), iz baza/rows.json.

Sastojci:
  minuti   = ponderisani prosek prethodnih minuta (novije utakmice teže, faktor DM po utakmici)
  učinak   = ponderisani učinak po minutu, skupljen ka polaznoj proceni (K pseudo-minuta);
             polazna procena je učinak iz prošle sezone skupljen ka proseku pozicije (K2),
             a za igrače bez prošle sezone prosek pozicije
  kontekst = odbrana protivnika prema poziciji za tu stavku (skupljeno n/(n+6)) na stepen B_OF
             * tempo (očekivani poeni utakmice / prosek lige) na stepen B_TEMPO
  očekivano mu = minuti * učinak * kontekst
  rasipanje: var = A * mu + C * mu^2 (C raste sa nestalnošću minuta), negativna binomna

Parametri su podešeni na verodostojnost svih učinaka iz kola 3 do 6 (ne na ponudama),
a provera je na ponudama (procene/skripte/provera.py).
"""
import bisect, collections, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, ucitaj, nk

STAVKE = 'PSA'
# podrazumevani parametri (prepisuju se iz procene/model_parametri.json ako postoji)
PAR = {
    'DM': 0.80,          # opadanje težine minuta po utakmici unazad
    'DR': 0.88,          # opadanje težine učinka po minutu
    'K': {'P': 60.0, 'S': 80.0, 'A': 80.0},       # pseudo-minuti ka proseku pozicije
    'B_OF': {'P': 0.5, 'S': 0.5, 'A': 0.5},       # težina odbrane protivnika
    'B_TEMPO': {'P': 0.6, 'S': 0.2, 'A': 0.4},    # težina tempa
    'A': {'P': 1.6, 'S': 1.0, 'A': 1.1},          # var = A*mu + C*mu^2
    'C': {'P': 0.06, 'S': 0.06, 'A': 0.10},
    'CV': 0.6,           # koliko nestalnost minuta (koef. varijacije) povećava C
    'K2': 150.0,         # pseudo-minuti kojima se prošla sezona skuplja ka proseku pozicije
    'MW': 1.0,           # težina minuta iz prošle sezone, u utakmicama
    'PRIOR': 1,          # 1 = polazna procena iz prošle sezone (procene/podaci/e2025_igraci.json)
    'KAL': {'P': [0.0, 1.0], 'S': [0.0, 1.0], 'A': [0.0, 1.0]},   # doterivanje: logit p' = a + b*logit p
}


def ucitaj_parametre():
    p = os.path.join(os.path.dirname(__file__), '..', 'model_parametri.json')
    if os.path.exists(p):
        for k, v in ucitaj(p).items():
            PAR[k] = v
    return PAR


class Baza:
    """Učitani rows.json i pomoćni indeksi."""

    def __init__(self, rows=None):
        rows = rows if rows is not None else ucitaj(os.path.join(BAZA, 'rows.json'))
        for r in rows:
            r['dan'] = r['d'][:10]
        self.rows = sorted(rows, key=lambda r: (r['d'], r['g']))
        self.byk = collections.defaultdict(list)
        for r in self.rows:
            self.byk[r['k']].append(r)
        self.dani = sorted({r['dan'] for r in self.rows})
        pp = os.path.join(os.path.dirname(__file__), '..', 'podaci', 'e2025_igraci.json')
        self.prosla = ucitaj(pp)['igraci'] if os.path.exists(pp) else {}
        self._kesh = {}
        # prezime -> ključevi
        self.po_prezimenu = collections.defaultdict(list)
        for k in self.byk:
            self.po_prezimenu[k.split()[-1]].append(k)

    # ---------- igrači ----------
    def nadji(self, ime, tim=None, dan=None):
        """Ključ igrača iz imena kod kladionice."""
        k = nk(ime)
        if k in self.byk:
            return k
        t = k.split()
        if not t:
            return None
        kand = self.po_prezimenu.get(t[-1], [])
        if len(t) > 1:
            kand2 = [c for c in kand if c[0] == t[0][0]] or kand
        else:
            kand2 = kand
        if tim:
            kt = [c for c in kand2 if any(r['team'] == tim for r in self.byk[c])]
            kand2 = kt or kand2
        if len(kand2) == 1:
            return kand2[0]
        # zamenjen redosled imena i prezimena ("Prezime Ime")
        if len(t) > 1:
            k2 = ' '.join(t[1:] + t[:1])
            if k2 in self.byk:
                return k2
            kand = [c for c in self.po_prezimenu.get(t[0], []) if c[0] == t[-1][0]]
            if len(kand) == 1:
                return kand[0]
        return None

    def pozicija(self, k):
        c = collections.Counter(r['pos'] for r in self.byk.get(k, []) if r['pos'] in 'GFC')
        return c.most_common(1)[0][0] if c else 'F'

    # ---------- liga pre dana ----------
    def liga(self, dan):
        """Prosek po minutu po poziciji, odbrana po poziciji, tempo — sve pre dana."""
        if dan in self._kesh:
            return self._kesh[dan]
        pre = [r for r in self.rows if r['dan'] < dan]
        # učinak po minutu po poziciji
        rate = {}
        for pos in 'GFC':
            rr = [r for r in pre if r['pos'] == pos]
            m = sum(r['min'] for r in rr) or 1
            rate[pos] = {s: sum(r[s] for r in rr) / m for s in STAVKE}
        # odbrana po poziciji: koliko protivnik dozvoljava poziciji po utakmici, u odnosu na ligu
        al = collections.defaultdict(lambda: collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0])))
        for r in pre:
            if r['pos'] in 'GFC':
                a = al[r['opp']][r['g']][r['pos']]
                a[0] += r['P']; a[1] += r['S']; a[2] += r['A']
        lg = {}
        for pos in 'GFC':
            vals = [al[t][g][pos] for t in al for g in al[t]]
            lg[pos] = [sum(v[i] for v in vals) / len(vals) if vals else 1 for i in range(3)]
        of = {}
        for t, gs in al.items():
            n = len(gs)
            of[t] = {}
            for pos in 'GFC':
                of[t][pos] = {}
                for i, s in enumerate(STAVKE):
                    m = sum(gs[g][pos][i] for g in gs) / n
                    of[t][pos][s] = 1 + ((m / lg[pos][i]) - 1) * n / (n + 6) if lg[pos][i] else 1
        # tempo: dati i primljeni poeni
        tg = collections.defaultdict(dict)
        for r in pre:
            d = tg[r['team']].setdefault(r['g'], {'pts': 0, 'opp': r['opp']})
            d['pts'] += r['P']
        tm = {}
        for t, gs in tg.items():
            pf = [d['pts'] for d in gs.values()]
            pa = [tg[d['opp']][g]['pts'] for g, d in gs.items() if g in tg.get(d['opp'], {})]
            n = len(pf)
            tm[t] = (sum(pf) / n, sum(pa) / len(pa) if pa else sum(pf) / n, n)
        lgp = sum(v[0] for v in tm.values()) / len(tm) if tm else 85.0
        out = dict(rate=rate, of=of, tm=tm, lgp=lgp)
        self._kesh[dan] = out
        return out

    # ---------- procena ----------
    def procena(self, k, dan, tim, protivnik, minuti=None, pos=None):
        """Procena za igrača k na dan (sve pre dana). minuti: ručno zadati očekivani minuti."""
        g = [r for r in self.byk.get(k, []) if r['dan'] < dan]
        if not g:
            return None
        pos = pos or self.pozicija(k)
        L = self.liga(dan)
        P = PAR
        n = len(g)
        # minuti
        w = [P['DM'] ** (n - 1 - i) for i in range(n)]
        mins = [r['min'] for r in g]
        em = sum(a * b for a, b in zip(w, mins)) / sum(w)
        sd = math.sqrt(sum(a * (b - em) ** 2 for a, b in zip(w, mins)) / sum(w)) if n > 1 else em * 0.35
        cv = min(1.0, sd / em) if em > 0 else 0.5
        if n < 3:
            cv = max(cv, 0.35)
        pr = self.prosla.get(k) if P.get('PRIOR') else None
        if pr and pr['n'] >= 3 and P['MW'] > 0:
            em = (sum(a * b for a, b in zip(w, mins)) + P['MW'] * pr['min'] / pr['n']) / (sum(w) + P['MW'])
        m_ocek = minuti if minuti is not None else em
        # tempo
        ta = L['tm'].get(tim); to = L['tm'].get(protivnik)
        tempo = ((ta[0] + to[1]) / 2 / L['lgp']) if ta and to else 1.0
        out = {'k': k, 'pos': pos, 'n': n, 'prosla': bool(pr), 'min': round(m_ocek, 1), 'min_cv': round(cv, 2), 'tempo': round(tempo, 3), 's': {}}
        wr = [P['DR'] ** (n - 1 - i) for i in range(n)]
        mw = sum(a * r['min'] for a, r in zip(wr, g))
        for s in STAVKE:
            prior = L['rate'][pos][s]
            if pr and pr['min'] > 0:
                prior = (pr[s] + P['K2'] * prior) / (pr['min'] + P['K2'])
            sw = sum(a * r[s] for a, r in zip(wr, g))
            rate = (sw + P['K'][s] * prior) / (mw + P['K'][s])
            of = L['of'].get(protivnik, {}).get(pos, {}).get(s, 1.0)
            ctx = (of ** P['B_OF'][s]) * (tempo ** P['B_TEMPO'][s])
            mu = max(0.05, m_ocek * rate * ctx)
            c = P['C'][s] * (1 + P['CV'] * cv)
            var = P['A'][s] * mu + c * mu * mu
            out['s'][s] = {'mu': round(mu, 2), 'var': round(var, 2), 'of': round(of, 3), 'rate36': round(rate * 36, 2),
                           'pros': round(sum(r[s] for r in g) / n, 2), 'poslednje': [r[s] for r in g[-5:]]}
        out['poslednji_min'] = [round(r['min']) for r in g[-5:]]
        return out


# ---------- raspodela ----------
def _nb_pmf_lista(mu, var, do):
    """Verovatnoće 0..do za negativnu binomnu sa datim mu i var (var>mu); inače Poisson."""
    if var <= mu * 1.0001:
        p0 = math.exp(-mu)
        out = [p0]
        for x in range(1, do + 1):
            out.append(out[-1] * mu / x)
        return out
    r = mu * mu / (var - mu)
    p = mu / var                      # verovatnoća „uspeha“ u parametrizaciji sa r
    out = [math.exp(r * math.log(p))]
    for x in range(1, do + 1):
        out.append(out[-1] * (x - 1 + r) / x * (1 - p))
    return out


def raspodela(mu, var):
    do = int(mu + 12 * math.sqrt(var) + 20)
    pm = _nb_pmf_lista(mu, var, do)
    s = sum(pm)
    return [x / s for x in pm]


def p_preko(mu, var, granica):
    """P(X > granica); za celobrojnu granicu (npr. 15) P(X >= 15) jer N+ znači „najmanje N“, pozovi sa 14.5."""
    pm = raspodela(mu, var)
    prag = math.floor(granica) + 1
    return sum(pm[prag:]) if prag < len(pm) else 0.0


def verovatnoca_preko(s, mu, var, granica):
    """P(X > granica) sa doterivanjem iz podešavanja (KAL), za stavku s."""
    p = min(max(p_preko(mu, var, granica), 1e-5), 1 - 1e-5)
    a, b = PAR.get('KAL', {}).get(s, [0.0, 1.0])
    z = a + b * math.log(p / (1 - p))
    return 1 / (1 + math.exp(-z))


def percentili(mu, var, qs=(0.1, 0.25, 0.5, 0.75, 0.9)):
    pm = raspodela(mu, var)
    out, c, i = [], 0.0, 0
    for q in qs:
        while i < len(pm) and c + pm[i] < q:
            c += pm[i]; i += 1
        out.append(i)
    return out


def log_ver(mu, var, x):
    pm = raspodela(mu, var)
    return math.log(max(pm[x] if x < len(pm) else 1e-12, 1e-12))
