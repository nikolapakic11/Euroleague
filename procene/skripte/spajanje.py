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
import collections, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, ucitaj, sacuvaj

# pravila za predloge (koriste ih tabla.py i predlozi.py)
KVOTA_MIN = 1.50
# Po utakmici do 6 predloga, najviše jedan po igraču, rangirano po spojenoj verovatnoći izabrane strane (nekalibrisanoj).
# Ulazi strana sa spojenom verovatnoćom bar PRAG, isto pravilo za PLUS i MINUS. Nema obaveznih PLUS predloga ni dopune
# do 4, a tim bez rotacionog igrača ne dobija MINUS (tabla.py). Na proveri po kolima 5 do 9 (spajanje podešeno samo na
# ranijim kolima): staro pravilo +10%, ovo +16% (procene/provera/izbor_2026-11-04.md). Donja granica vrednosti (EV)
# i izbor po kalibrisanoj verovatnoći su tamo bili lošiji, pa se ne koriste.
# Za prikaz se verovatnoća kalibriše (kal, Platt po stavci), jer je spojena previše samouverena.
PRAG = {'u': 0.53, 'o': 0.53}
MIN_UT, MAX_UT = 6, 6   # odluka 4.11.2026: 6 predloga po utakmici je minimum (dopuna, izbor_utakmice)
PLUS_MIN = 2          # odluka 4.11.2026: bar 2 PLUS po utakmici (stranica je za ljude, ne samo minusi)
PLUS_POD = 0.45       # obavezni PLUS ne ide ispod ove spojene verovatnoće
MAX_ISTA = 2          # najviše 2 predloga iste stavke i strane po utakmici (raznovrsnost)
MAX_TIM = 4           # najviše 4 predloga iz istog tima po utakmici
NIVOI = ((0.62, 'jak'), (0.56, 'solidan'))      # na kalibrisanoj verovatnoći; ispod 0,56: „nagoveštaj“


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


def kalibrisi(p, kal, s):
    """Platt po stavci: logit p' = a + b·logit p (kal = {s: [a, b]}); bez kal vraća p."""
    if not kal or s not in kal:
        return p
    a, b = kal[s]
    return 1 / (1 + math.exp(-(a + b * lg(p))))


def preko_kal(w, kal, s, pm, tr):
    return kalibrisi(preko(w, s, pm, tr), kal, s)


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
    """kand: dict(igr, s, strana, pp, ev, k, tim) za jednu utakmicu; pp je nekalibrisana spojena verovatnoća (za izbor).
    Vraća do MAX_UT predloga, najviše jedan po igraču, sa poljem rang. Po igraču i strani se uzima stavka sa najvećom
    verovatnoćom (za istu stavku i stranu najbolja cena). Pravilo od 4.11.2026 (Nikola): stranica je za ljude, pa
    moraju da budu i PLUS predlozi i raznovrsnost:
      - bar PLUS_MIN najboljih PLUS (po verovatnoći), i kad su ispod praga i kad su MINUS predlozi jači; donja
        granica za takav PLUS je PLUS_POD;
      - ostala mesta MINUS i PLUS sa verovatnoćom ≥ PRAG, po verovatnoći;
      - najviše MAX_ISTA predloga iste stavke i strane (npr. skokovi MINUS) i najviše MAX_TIM iz istog tima.
    Nivo se dodeljuje posle, na kalibrisanoj verovatnoći (tabla.py)."""
    po_stavci = {}
    for c in kand:
        if c['k'] < KVOTA_MIN:
            continue
        kl = (c['igr'], c['s'], c['strana'])
        if kl not in po_stavci or c['ev'] > po_stavci[kl]['ev']:      # najbolja cena za istu stavku i stranu
            po_stavci[kl] = c
    red = sorted(po_stavci.values(), key=lambda c: (-c['pp'], -c['ev']))
    izabrani, igraci, ista, timovi = [], set(), collections.Counter(), collections.Counter()

    def moze(c):
        return (c['igr'] not in igraci and ista[(c['s'], c['strana'])] < MAX_ISTA
                and (not c.get('tim') or timovi[c['tim']] < MAX_TIM))

    def uzmi(c):
        izabrani.append(c); igraci.add(c['igr']); ista[(c['s'], c['strana'])] += 1
        if c.get('tim'):
            timovi[c['tim']] += 1

    for c in red:                                      # obavezni PLUS
        if sum(1 for x in izabrani if x['strana'] == 'o') >= PLUS_MIN:
            break
        if c['strana'] == 'o' and c['pp'] >= PLUS_POD and moze(c):
            uzmi(c)
    for c in red:                                      # ostala mesta
        if len(izabrani) >= MAX_UT:
            break
        if c['pp'] >= PRAG[c['strana']] and moze(c):
            uzmi(c)
    # MIN_UT je najmanji broj predloga (odluka 4.11.2026: 6). Ako ih nema dovoljno, ograničenja se popuštaju redom:
    # najpre broj iz istog tima (npr. kad se igra samo jedna utakmica, a jedan tim je bez MINUS), pa broj iste stavke
    # i strane, i na kraju prag (dopuna najboljim preostalim, ne ispod PLUS_POD; takav predlog dobija nivo „slab“).
    for korak in ('tim', 'ista', 'prag'):
        for c in red:
            if len(izabrani) >= MIN_UT:
                break
            if c['igr'] in igraci:
                continue
            if korak != 'prag' and c['pp'] < PRAG[c['strana']]:
                continue
            if korak == 'prag' and c['pp'] < PLUS_POD:
                continue
            if korak == 'tim' and ista[(c['s'], c['strana'])] >= MAX_ISTA:
                continue
            uzmi(c)
            if korak == 'prag' or c['pp'] < PRAG[c['strana']]:
                c['slab'] = True
    L = sorted(izabrani, key=lambda c: (-c['pp'], -c['ev']))
    return [dict(c, nivo=nivo(c['pp'], slab=c.get('slab', False)), rang=r) for r, c in enumerate(L, 1)]


def platt(X, l2=20.0):
    """X: dict(p, y). Vraća [a, b] za logit p' = a + b·logit p; L2 kazna ka a=0, b=1."""
    a, b = 0.0, 1.0
    for _ in range(50):
        ga = -l2 * a; gb = -l2 * (b - 1); haa = l2; hbb = l2; hab = 0.0
        for x in X:
            z0 = lg(x['p']); p = 1 / (1 + math.exp(-(a + b * z0))); e = x['y'] - p; v = p * (1 - p)
            ga += e; gb += e * z0; haa += v; hab += v * z0; hbb += v * z0 * z0
        det = haa * hbb - hab * hab
        a += (hbb * ga - hab * gb) / det; b += (haa * gb - hab * ga) / det
    return [round(a, 4), round(b, 4)]


def predlozi_unazad(w, R, g_od, kal=None):
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

    # kalibracija: walk-forward predviđanja (spajanje podešeno samo na ranijim kolima), pa Platt po stavci,
    # skupljen ka (0, 1) da mala stavka ne ode u krajnost
    kola = sorted({r['kolo'] for r in R})
    wf = []
    for k in kola:
        ranije = [r for r in R if r['kolo'] < k]
        if len(ranije) < 300:
            continue
        w_k = podesi(ranije)
        wf += [dict(s=r['s'], p=preko(w_k, r['s'], r['pm'], r['tr']), y=r['preko']) for r in R if r['kolo'] == k]
    kal = {s: platt([x for x in wf if x['s'] == s]) for s in 'PSA'}

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
    out = dict(w=w_sve, kal=kal, n_wf=len(wf), w_kola_4_6=w_tr, n_granica=len(R), pravilo=dict(kvota_min=KVOTA_MIN, prag_minus=PRAG['u'], prag_plus=PRAG['o'], min_ut=MIN_UT, max_ut=MAX_UT, plus_min=PLUS_MIN,
                                                               nivoi=[[g, n] for g, n in NIVOI]), test=test)
    sacuvaj(os.path.join(PROCENE, 'spajanje.json'), out)
    print(json.dumps(out, ensure_ascii=False, indent=1))


if __name__ == '__main__':
    main()
