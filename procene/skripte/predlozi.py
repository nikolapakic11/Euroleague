"""Javni predlozi po kolu: PLUS (preko) i MINUS (ispod), poeni, skokovi i asistencije.

  python3 procene/skripte/predlozi.py --kolo 11      (posle tabla.py --kolo 11)
  python3 procene/skripte/predlozi.py                 (samo osvežava ishode i stranicu)

Pravilo (procene/skripte/spajanje.py, izbor_utakmice), izbor se pravi u tabli (tabla.py):
  - 4 do 6 predloga po utakmici, najviše jedan po igraču, rangirano po spojenoj verovatnoći izabrane strane
  - strana ulazi sa spojenom verovatnoćom bar 53% (MINUS) odnosno 50% (PLUS), kvota bar 1,50; do 2 PLUS imaju mesto unapred
  - nivoi: jak (bar 60%), solidan (55–60%), nagoveštaj (ispod 55%), slab (dopuna do 4, ispod praga)
  - uz svaki predlog: ostale kladionice sa istom granicom, opseg ponuđenih granica i „soft spot“
Predlozi za utakmicu se zaključavaju kad utakmica počne. Ishodi se upisuju iz baza/rows.json.
Izlaz: procene/predlozi/kolo<N>.json i procene/javno/predlozi.html (iz procene/javno/sablon.html).
"""
import argparse, collections, datetime as dt, glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import model
import obrazlozenje as OB
from model import Baza, verovatnoca_preko, percentili, raspodela
from zajedno import PROCENE, BG, ucitaj, sacuvaj
import spajanje

IME_KL = {'admiral': 'Admiral', 'maxbet': 'MaxBet', 'mozzart': 'Mozzart', 'soccerbet': 'Soccerbet'}


POZM = {'G': 'bekovima', 'F': 'krilima', 'C': 'centrima'}
POZ1 = {'G': 'bek', 'F': 'krilo', 'C': 'centar'}
SNA = {'P': 'poena', 'S': 'skokova', 'A': 'asistencija'}


def zr(x, d=1):
    """Broj u srpskom zapisu (zarez)."""
    s = f'{x:.{d}f}'.replace('.', ',')
    return s[:-2] if d == 1 and s.endswith(',0') else s


def broj_tacaka(pp):
    """Koliko razloga navesti: jači izgledi, više obrazloženja (verovatnoća je kalibrisana)."""
    return 6 if pp >= 0.62 else 5 if pp >= 0.56 else 3


def naginje(x):
    """Strana na koju naginje igrač u stavci, na najčešćoj glavnoj granici: dict(strana, l, pp, knjige) ili None."""
    if x.get('ng_spoj'):                        # objavljen predlog izabran po spoju: prikaz igrača prati predlog
        return dict(x['ng_spoj'])
    L = [z for z in x['linije'] if z.get('m', 1)]
    if not L:
        return None
    c = collections.Counter(z['l'] for z in L)
    l = sorted(c, key=lambda v: (-c[v], v))[0]
    pc = sum(z['pc'] for z in L if z['l'] == l) / c[l]
    # od 6.11.2026 (Nikola: „očekuješ 4,3, a naginje preko 5,5“): strana se prikazuje samo kad se model i zbirna
    # verovatnoća slažu i kad je zbirna bar 53%; inače je „neodlučno“ (model jedno, kladionice drugo)
    pm = sum(z.get('pm', pc) for z in L if z['l'] == l) / c[l]
    fer = sum(z.get('trk', z.get('tr', pc)) for z in L if z['l'] == l) / c[l]
    # od 6.11.2026 (objedinjen prikaz): prikazano očekivanje je usklađeno sa zbirnom verovatnoćom, pa je strana uvek
    # dosledna očekivanju; „bez jasne strane“ kad je verovatnoća ispod 53%
    neodl = max(pc, 1 - pc) < 0.53
    return dict(strana='o' if pc >= 0.5 else 'u', l=l, pp=round(max(pc, 1 - pc), 3), pm=round(pm, 3), fer=round(fer, 3),
                neodl=neodl)


def rucni_pred(x, strana, l=None):
    """Predlog za ručno dodatu stavku (Nikola) koju tabla nije izabrala: granica l (ili najčešća glavna), najbolja kvota
    za stranu, verovatnoća iz spoja (prosek kladionica na toj granici). Od 11.11.2026."""
    L = [z for z in x['linije'] if z.get('m', 1)]
    if l is None and L:
        c = collections.Counter(z['l'] for z in L)
        l = sorted(c, key=lambda v: (-c[v], v))[0]
    Z = [z for z in L if z['l'] == l]
    if not Z:
        return None
    po = sum(z['pc'] for z in Z) / len(Z)
    fer_o = sum(z.get('trk', z['tr']) for z in Z) / len(Z)
    kv = lambda z: z['o'] if strana == 'o' else z['u']
    b = max(Z, key=kv)
    pp = po if strana == 'o' else 1 - po
    red_kl = {k: n for n, k in enumerate(('admiral', 'maxbet', 'mozzart', 'soccerbet'))}
    return dict(strana=strana, pp=round(pp, 3), ps=round(pp, 3), ev=round(pp * kv(b) - 1, 3), kvota=kv(b),
                fer=round(fer_o if strana == 'o' else 1 - fer_o, 4), l=l, kl=b['kl'], nivo=spajanje.nivo(pp), rang=None,
                ostale=sorted([dict(kl=z['kl'], k=kv(z)) for z in Z if z['kl'] != b['kl']], key=lambda t: -t['k']),
                knjige=sorted([dict(kl=z['kl'], l=z['l'], u=z['u'], o=z['o']) for z in L], key=lambda t: red_kl.get(t['kl'], 9)),
                opseg=[], soft=None, rucno=True)


def podoban(i):
    """Isti uslov kao u tabli: igra, nije upitan, nije izostao iz poslednjih utakmica (osim ako ga izveštaj potvrđuje),
    ima bar 3 utakmice (novajlija sa prošlom sezonom ili ručno zadatim minutima: 2)."""
    potvrdjen = i.get('izvestaj') == 'igra'
    return not (i['ne_igra'] or i.get('upitan') or (i['odsutan'] > 0 and not potvrdjen)
                or (i['n'] < 3 and not ((i.get('novajlija') or i.get('rucno_min')) and i['n'] >= 2)))


def uskladi(s, mu0, var0, l, cilj):
    """Očekivanje (sredina raspodele) i raspon koji odgovaraju verovatnoći za PREKO = cilj na granici l; isti postupak
    kao u tabli (oblik raspodele modela, pomeren). Vraća (mu, q)."""
    vr = lambda m: max(var0 * m / mu0 if mu0 > 0 else var0, m * 1.0001)
    lo, hi = 0.05, max(3 * l + 3, mu0 * 3 + 3)
    for _ in range(40):
        md = (lo + hi) / 2
        if verovatnoca_preko(s, md, vr(md), l) < cilj:
            lo = md
        else:
            hi = md
    sr = (lo + hi) / 2
    var_o = round(vr(sr), 2)
    pmf = raspodela(sr, var_o)
    F, j = 0.0, 0
    while j < len(pmf) and F + pmf[j] < 0.5:
        F += pmf[j]; j += 1
    med = j - 0.5 + ((0.5 - F) / pmf[j] if j < len(pmf) and pmf[j] > 0 else 0.5)
    return round(med, 2), percentili(sr, var_o)


def izaberi(tabla, K=None, sve=False):
    """Predlozi su već izabrani u tabli (tabla.py, pravilo spajanje.izbor_utakmice); ovde se samo prepisuju, uz analizu.
    Ručno dodati (iskljuceni.json, "dodati") ulaze i kad ih tabla nije izabrala (rucni_pred)."""
    out = []
    dod = iskljuceni().get('dodati', {})
    for u in tabla['utakmice']:
        if u['pocela'] and not sve:
            continue
        rucni = {(x['k'], x['s']): x for x in dod.get(u['dan'], [])}
        for st in u['strane']:
            tudja = next(x for x in u['strane'] if x is not st)
            for i in st['igraci']:
                for s in 'PSA':
                    pr0 = i['s'][s].get('pred')
                    x_r = rucni.get((i['k'], s))
                    if x_r and (not pr0 or pr0['strana'] != x_r.get('strana', pr0['strana']) or (x_r.get('l') is not None and pr0['l'] != x_r['l'])):
                        pr0 = rucni_pred(i['s'][s], x_r.get('strana', 'u'), x_r.get('l')) or pr0
                    kand = [(pr0, False)] if pr0 else []
                    # od 13.11.2026: izbor za sajt ide po naučenom spoju (izbor_dana), pa su kandidati obe strane svake
                    # stavke na najčešćoj glavnoj granici (skokovi samo ispod); iz_kand = tabla ga nije izabrala
                    if i['s'][s].get('linije') and podoban(i):
                        for strana in ('u', 'o'):
                            if (strana == 'o' and s == 'S') or (pr0 and pr0['strana'] == strana):
                                continue
                            gk = rucni_pred(i['s'][s], strana)
                            if gk:
                                gk['rucno'] = False
                                kand.append((gk, True))
                    for pr, iz_k in kand:
                        z = next((z for z in i['s'][s]['linije'] if z['kl'] == pr['kl'] and z['l'] == pr['l']), {})
                        an = OB.analiza(i, s, pr, u, st, tudja, K, broj_tacaka(pr['pp'])) if K and not iz_k else []
                        out.append(dict(g=u['g'], dan=u['dan'], vreme=u['vreme'], k=i['k'], ime=i['ime'], tim=st['tim'], prot=st['prot'],
                                        s=s, strana=pr['strana'], l=pr['l'], kl=pr['kl'], kvota=pr['kvota'], pp=pr['pp'], ev=pr['ev'],
                                        nivo=pr['nivo'], rang=pr['rang'], fer=pr.get('fer'), ostale=pr.get('ostale', []), knjige=pr.get('knjige', []), soft=pr.get('soft'),
                                        opseg=pr.get('opseg', []), q=i['s'][s]['q'], mu=i['s'][s]['mu'], min=i['min'],
                                        pm=z.get('pm'), tr=z.get('tr'), l0=z.get('l0'), vatra=i['s'][s].get('vatra'),
                                        pos=i['pos'], of=i['s'][s]['of'], analiza=an, iz_kand=iz_k,
                                        mu_m=i['s'][s].get('mu_m', i['s'][s]['mu']), var=i['s'][s].get('var'),
                                        podoban=podoban(i), novi_saigrac=bool(i.get('novi_saigrac'))))
                        Z = [zz for zz in i['s'][s]['linije'] if zz.get('m', 1) and zz['l'] == pr['l'] and zz.get('pm') is not None]
                        if Z:                              # model procena i tržište: prosek kladionica na toj granici (verovatnoća PREKO)
                            out[-1]['pm'] = round(sum(zz['pm'] for zz in Z) / len(Z), 4)
                            out[-1]['fer_o'] = round(sum(zz.get('trk', zz['tr']) for zz in Z) / len(Z), 4)
    return out


# Predlozi za dan (odluka 6.11.2026, provera kvote_2026-11-06.txt): rang po PREDNOSTI nad tržištem (naša verovatnoća
# minus fer verovatnoća iz kvota svih kladionica), a ne po samoj verovatnoći, jer po verovatnoći izbor ide na najniže kvote.
# Ulazi strana sa prednošću bar DAN_PREDNOST i verovatnoćom bar DAN_PRAG; najmanje DAN_NAJMANJE, najviše DAN_MAX;
# najviše 4 iz utakmice, 2 iz tima. PLUS nije obavezan; dodaje se do DAN_PLUS najboljih PLUS sa verovatnoćom bar
# DAN_PRAG i prednošću bar DAN_PLUS_PREDNOST. Walk-forward kola 5–10: 60,6%, +17,8%, prosečna kvota 1,95
# (po verovatnoći: 60,8%, +2,3%, kvota 1,69). Isto pravilo i za dan sa jednom utakmicom.
# Od 7.11.2026 (provera/logika_2026-11-06.md): prednost bar 6%; PLUS signali modela nemaju vrednost (kad je model iznad
# tržišta, preko ne prolazi češće od tržišta), pa nema „poželjnog PLUS-a“, a PLUS ulazi samo sa prednošću bar 8%
# (ručno dodat ide uvek, uz tvrd razlog).
DAN_PRAG, DAN_PREDNOST, DAN_NAJMANJE, DAN_MAX = 0.54, 0.06, 4, 12
DAN_PLUS, DAN_PLUS_PREDNOST = 0, 0.08
DAN_PO_UT, DAN_PO_TIMU, DAN_PO_STAVCI = 4, 2, 12
DAN_NISKA, DAN_NISKE_MAX = 1.65, 3   # najviše 3 predloga sa kvotom ispod 1,65 za dan (Nikola, 6.11.: ne sme sve najniže kvote)
DAN_FORMA_N, DAN_FORMA_MIN = 7, 0.5            # u poslednjih 7 utakmica bar polovina na stranu predloga
DAN_ZADRZI = 0.02                              # već objavljen predlog ostaje dok ga novi ne nadmaši za bar 2 poena procenta
# Slaganje sa minus-modelom (od 7.11.2026, objedinjeni projekti; provera spoj/provera/izvestaj.md): MINUS ulazi samo
# kad i minus-model (prepis Generatora iz aplikacije za minuse, spoj/minus_model.py) vidi ispod bar prosečno
# (msig >= MSIG_PRAG, medijana). Kandidati po ovom pravilu sa kojima se minus-model nije slagao prolazili su ~52%
# (kola 5-7 i 8-10 posebno), a oni sa kojima se slaže 63-64% i 62-63%. Minus-model posebno ispravlja igrače bez prošle
# sezone u Evroligi, gde model procena greši. PLUS bez promene (minus-model okrenut za plus nema vrednost).
DAN_MINUS_SLAGANJE = True
# IZBOR ZA SAJT PO NAUČENOM SPOJU (od 13.11.2026, spoj/analiza/IZVESTAJ_2026-11-13.md). Do tada: MINUS po prednosti
# modela procena nad tržištem (uz slaganje minus-modela), PLUS po prednosti modela procena (na sajtu: MINUS 9/15, PLUS 5/13).
#  MINUS: verovatnoća po spoju (signali.spoj2: tržište + oba modela + izostanci + granica prema proseku + trend minuta,
#         forma, tempo, kolebanje minuta), poređano po VEROVATNOĆI, ne po prednosti (po prednosti idu više kvote i ~60%,
#         po verovatnoći ~68%, uz sličan povraćaj). Uslovi: kvota ≥ 1,60, minus-model se slaže (msig ≥ 0,35), timu ne
#         fali 35+ minuta rotacije. Najviše 4 dnevno, 2 po utakmici, 2 po timu. Bez skokova: skokovi ispod koje spoj
#         najviše ceni ne prolaze češće od ostalih (druga polovina sezone 45–51%), asistencije 77%, poeni 66%.
#  PLUS:  samo poeni i asistencije, verovatnoća za preko po spoju ≥ 55%; jedan dnevno, drugi samo uz ≥ 65%.
#         Po prednosti modela procena najbolji PLUS dana prolazi 47%, po spoju 13/17. Spoj za preko najviše gura:
#         saigrači koji fale, granica iznad proseka igrača (kladionica je digla jer mu raste uloga), minuti u padu.
# Provera (kola 4–11, 17 dana): staro pravilo MINUS 62%; novo 88% bez tog kola i 24/28 strogo unapred, ali su pravila
# birana na istim podacima, pa su te brojke precenjene. Na sačuvanim tablama kola 10–11 (5 dana) novo pravilo: MINUS
# 13/18, PLUS 2/4. Realno očekivanje: MINUS 65–70%, PLUS oko 60%. Pratiti; preispitati posle 40 novih predloga.
SAJT_SPOJ = True
SAJT_MINUS_N, SAJT_MINUS_PRAG, SAJT_MINUS_SKOKOVI, SAJT_PO_UT = 4, 0.58, 0, 2
SAJT_PLUS_PRAG, SAJT_PLUS_DRUGI = 0.55, 0.65
SAJT_KVOTA = 1.60
_SIG = {}
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'spoj'))
from minus_model import MinusModel, MSIG_PRAG
_MM = {}
IZBACENI_MM = {}                               # dan -> MINUS kandidati koje je izbacio minus-model (za proveru)


def minus_signal(B, p):
    """msig minus-modela za MINUS kandidata p (k, dan, tim, prot, s, l, fer); None ako nema podataka."""
    if not p.get('prot'):
        return None
    mm = _MM.get(id(B))
    if mm is None:
        mm = _MM[id(B)] = MinusModel(B)
    fu = p.get('fer') or min(0.9, 1 / p['kvota'] / 1.05)
    r = mm.procena(p['k'], p['dan'], p['tim'], p['prot'], p['s'], p['l'], fu)
    return r['msig'] if r else None


def spoj_ocene(P, B):
    """Svakom kandidatu upisuje ps (verovatnoća njegove strane po naučenom spoju), msig i izostanci_tim."""
    import signali
    if _SIG.get('B') is not B:
        _SIG.clear()
        _SIG['B'] = B
        _SIG['S'] = signali.Signali(B)
        try:
            pp = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'podaci', 'povrede.json')
            _SIG['pov'] = {k: dict(v) for k, v in ucitaj(pp)['igraci'].items()}
        except Exception:
            _SIG['pov'] = {}
    S, pov = _SIG['S'], _SIG['pov']
    for p in P:
        p['ps'] = None
        fo = p.get('fer_o')
        if fo is None and p.get('fer') is not None:
            fo = p['fer'] if p['strana'] == 'o' else 1 - p['fer']
        if fo is None or not p.get('prot'):
            continue
        fu = min(max(1 - fo, 0.02), 0.98)
        r = S.minus(p['k'], p['dan'], p['tim'], p['prot'], p['s'], p['l'], fu)
        p['msig'] = r['msig'] if r else None
        kljuc = (p['tim'], p['dan'])
        if kljuc not in _SIG:
            _SIG[kljuc] = signali.izostanci(S, p['tim'], p['dan'], pov)
        miss = sum(m for k, m in _SIG[kljuc].items() if k != p['k'])
        spu = p.get('l0') is not None and p['l'] < p['l0']
        pu = signali.spoj2(fu, p.get('pm'), p['msig'], miss, signali.zline(S, p['k'], p['dan'], p['s'], p['l']), p['s'], p['l'],
                           signali.dodatne(S, p['k'], p['tim'], p['prot'], p['dan'], p['s']), spu)
        p['ps'] = round(pu if p['strana'] == 'u' else 1 - pu, 4)
        p['izostanci_tim'] = round(miss)


def izbor_spoj(P, B, ranije, van, isk):
    """Izbor dana po naučenom spoju (SAJT_*). P: kandidati oba smera; vraća izabrane sa pp = verovatnoća po spoju."""
    import signali
    ist = lambda p: (p['k'], p['s'], p['strana'], p['l'])
    spoj_ocene(P, B)
    K = [p for p in P if not van(p) and p.get('ps') is not None and p['kvota'] >= SAJT_KVOTA and p.get('podoban', True)]
    oc = lambda p: p['ps'] + (DAN_ZADRZI if ist(p) in ranije else 0)
    M = sorted([p for p in K if p['strana'] == 'u' and oc(p) >= SAJT_MINUS_PRAG], key=lambda p: -oc(p))
    van_mm = [p for p in M if p.get('msig') is not None and p['msig'] < MSIG_PRAG]
    if P:
        IZBACENI_MM[P[0]['dan']] = [dict(k=p['k'], ime=p.get('ime'), tim=p['tim'], s=p['s'], l=p['l'], kvota=p['kvota'], kl=p.get('kl'),
                                         pp=p['ps'], fer=p.get('fer'), msig=p['msig']) for p in van_mm[:15]]
    M = [p for p in M if p not in van_mm and p.get('izostanci_tim', 0) < signali.IZOSTANCI_PRAG]
    izab = []
    for p in M:
        if len(izab) >= SAJT_MINUS_N:
            break
        if (all(q['k'] != p['k'] for q in izab) and sum(q['g'] == p['g'] for q in izab) < SAJT_PO_UT
                and sum(q['tim'] == p['tim'] for q in izab) < DAN_PO_TIMU
                and (p['s'] != 'S' or sum(q['s'] == 'S' for q in izab) < SAJT_MINUS_SKOKOVI)):
            izab.append(p)
    O = sorted([p for p in K if p['strana'] == 'o' and p['s'] in 'PA' and oc(p) >= SAJT_PLUS_PRAG and not p.get('novi_saigrac')],
               key=lambda p: -oc(p))
    npl = 0
    for p in O:
        if npl >= 2 or (npl == 1 and p['ps'] < SAJT_PLUS_DRUGI):
            break
        if all(q['k'] != p['k'] for q in izab) and not any(q['strana'] == 'o' and q['tim'] == p['tim'] for q in izab):
            izab.append(p)
            npl += 1
    for p in izab:
        p['spoj'] = True
        p['pp'] = round(p['ps'], 3)
        p['nivo'] = spajanje.nivo(p['pp'])
        p['ev'] = round(p['pp'] * p['kvota'] - 1, 3)
        if p.get('var') and p.get('mu_m') is not None:      # prikazano očekivanje odgovara verovatnoći predloga
            p['mu'], p['q'] = uskladi(p['s'], p['mu_m'], p['var'], p['l'], p['pp'] if p['strana'] == 'o' else 1 - p['pp'])
    for x in isk.get('dodati', {}).get(P[0]['dan'] if P else '', []):     # ručno dodati (Nikola)
        for p in P:
            if (p['k'] == x['k'] and p['s'] == x['s'] and p['strana'] == x.get('strana', 'u')
                    and (x.get('l') is None or p['l'] == x['l']) and p not in izab):
                p['rucno'] = True
                izab.append(p)
                break
    for p in izab:
        p['forma'] = list(forma(B, p))
    izab.sort(key=lambda p: -p['pp'])
    for i, p in enumerate(izab, 1):
        p['rang_dan'] = i
    return izab


def primeni_spoj(tabla, P):
    """Objavljeni predlozi izabrani po spoju određuju prikaz tog igrača u tabli (strana, verovatnoća, očekivanje, raspon),
    da stranica svuda govori isto. Menja tablu u memoriji."""
    M = {(p['g'], p['k'], p['s']): p for p in P if p.get('spoj') and p.get('ishod') is None}
    for u in tabla['utakmice']:
        for st in u['strane']:
            for i in st['igraci']:
                for s in 'PSA':
                    p = M.get((u['g'], i['k'], s))
                    if not p:
                        continue
                    x = i['s'][s]
                    Z = [z for z in x['linije'] if z.get('m', 1) and z['l'] == p['l']]
                    x['mu'], x['q'] = p['mu'], p['q']
                    x['ng_spoj'] = dict(strana=p['strana'], l=p['l'], pp=p['pp'], neodl=False,
                                        pm=round(sum(z.get('pm', z['pc']) for z in Z) / len(Z), 3) if Z else p.get('pm'),
                                        fer=round(sum(z.get('trk', z.get('tr', z['pc'])) for z in Z) / len(Z), 3) if Z else p.get('fer_o'))
                    x['pred'] = dict(strana=p['strana'], pp=p['pp'], ps=p['pp'], ev=p['ev'], kvota=p['kvota'], fer=p.get('fer'), l=p['l'],
                                     kl=p['kl'], nivo=p['nivo'], rang=p.get('rang'), ostale=p.get('ostale', []), knjige=p.get('knjige', []),
                                     opseg=p.get('opseg', []), soft=p.get('soft'))


def forma(B, p):
    """Koliko je puta u poslednjih DAN_FORMA_N utakmica igrač bio na strani predloga (na granici predloga)."""
    G = [r for r in B.byk.get(p['k'], []) if r['dan'] < p['dan']][-DAN_FORMA_N:]
    pog = sum((r[p['s']] > p['l']) if p['strana'] == 'o' else (r[p['s']] < p['l']) for r in G)
    return pog, len(G)


ISKLJ_PUT = os.path.join(PROCENE, 'podaci', 'iskljuceni.json')


def iskljuceni():
    """Ručno isključeni predlozi (Nikola): {"<dan>": [{"k": "ime malim slovima", "s": "S", "razlog": "..."}]}; bez "s" ceo igrač.
    Ručno dodati (ključ "dodati"): {"dodati": {"<dan>": [{"k": ..., "s": ..., "strana": "o"|"u"}]}}: ulaze bez praga i ograničenja."""
    try:
        return ucitaj(ISKLJ_PUT) if os.path.exists(ISKLJ_PUT) else {}
    except Exception:
        return {}


def izbor_dana(P, B=None, ranije=()):
    """P: predlozi jednog dana. Vraća izabrane, poređane po verovatnoći, uz rang_dan.
    Ručno isključeni (procene/podaci/iskljuceni.json) ne ulaze, a mesto dobija sledeći po pravilu.
    Predlog čija skorija forma govori suprotno (manje od polovine poslednjih utakmica na strani predloga) ne ulazi."""
    ist = lambda p: (p['k'], p['s'], p['strana'], p['l'])
    ranije = set(ranije)
    pred = lambda p: p['pp'] - (p['fer'] if p.get('fer') is not None else 0.5)
    ocena = lambda p: pred(p) + (DAN_ZADRZI if ist(p) in ranije else 0)
    isk = iskljuceni()
    van = lambda p: any(x['k'] == p['k'] and x.get('s', p['s']) == p['s'] for x in isk.get(p['dan'], []) if isinstance(x, dict))
    P_rucno = list(P)                            # ručno dodati ulaze bez praga, forme i minus-modela (od 11.11.2026)
    if SAJT_SPOJ and B is not None:
        return izbor_spoj(P_rucno, B, ranije, van, isk)
    P = sorted([p for p in P if p.get('nivo') != 'slab' and not van(p) and not p.get('iz_kand')], key=lambda p: -ocena(p))
    if B is not None:
        for p in P_rucno:
            p['forma'] = list(forma(B, p))
        P = [p for p in P if p['forma'][1] < 4 or p['forma'][0] / p['forma'][1] >= DAN_FORMA_MIN]
    if B is not None and DAN_MINUS_SLAGANJE:
        for p in P:
            if p['strana'] == 'u':
                p['msig'] = minus_signal(B, p)
        van_mm = [p for p in P if p['strana'] == 'u' and p.get('msig') is not None and p['msig'] < MSIG_PRAG]
        if P:
            IZBACENI_MM[P[0]['dan']] = [dict(k=p['k'], ime=p.get('ime'), tim=p['tim'], s=p['s'], l=p['l'], kvota=p['kvota'], kl=p.get('kl'),
                                             pp=p['pp'], fer=p.get('fer'), msig=p['msig']) for p in van_mm]
        P = [p for p in P if p not in van_mm]

    def moze(p, izab):
        return (all(q['k'] != p['k'] for q in izab) and sum(q['g'] == p['g'] for q in izab) < DAN_PO_UT and sum(q['tim'] == p['tim'] for q in izab) < DAN_PO_TIMU
                and sum((q['s'], q['strana']) == (p['s'], p['strana']) for q in izab) < DAN_PO_STAVCI
                and (p['kvota'] >= DAN_NISKA or sum(q['kvota'] < DAN_NISKA for q in izab) < DAN_NISKE_MAX)
                and (p['strana'] != 'o' or ocena(p) >= DAN_PLUS_PREDNOST))
    izab = []
    for p in P:                                   # prvo svi koji prolaze prag
        if len(izab) >= DAN_MAX:
            break
        if ocena(p) >= DAN_PREDNOST and p['pp'] >= DAN_PRAG and moze(p, izab):
            izab.append(p)
    for x in isk.get('dodati', {}).get(P_rucno[0]['dan'] if P_rucno else '', []):     # ručno dodati (Nikola)
        for p in P_rucno:
            if p['k'] == x['k'] and p['s'] == x['s'] and p['strana'] == x.get('strana', p['strana']) and p not in izab:
                p['rucno'] = True
                izab.append(p)
                break
    for p in P:                                   # dopuna do najmanjeg broja, najbolji preostali
        if len(izab) >= DAN_NAJMANJE:
            break
        if p not in izab and moze(p, izab):
            izab.append(p)
    for p in P:                                   # poželjan PLUS, ako je dovoljno dobar
        if sum(q['strana'] == 'o' for q in izab) >= DAN_PLUS:
            break
        if (p['strana'] == 'o' and p not in izab and p['pp'] >= DAN_PRAG and ocena(p) >= DAN_PLUS_PREDNOST
                and moze(p, izab)):
            izab.append(p)
    izab.sort(key=lambda p: -p['pp'])
    for i, p in enumerate(izab, 1):
        p['rang_dan'] = i
    return izab


def javni_kodovi(x):
    """Na javnoj stranici timovi nose zvanične skraćenice Evrolige (tvCode iz rasporeda: IST -> EFS, MAD -> RMB, ...).
    Menjaju se vrednosti polja tim, prot, dom, gost, team, opp, protivnik iz zadnjih utakmica i ključevi tabele timova."""
    from zajedno import BAZA
    g = ucitaj(os.path.join(BAZA, 'games.json'))
    M = {}
    for u in (g['data'] if isinstance(g, dict) else g):
        for s in ('local', 'road'):
            c = u[s]['club']
            M[c['code']] = c.get('tvCode') or c['code']
    POLJA = {'tim', 'prot', 'dom', 'gost', 'team', 'opp'}
    def tr(v, roditelj=None):
        if isinstance(v, dict):
            out = {}
            for k, w in v.items():
                k2 = M.get(k, k) if roditelj == 'timovi' else k
                out[k2] = M.get(w, w) if (k in POLJA and isinstance(w, str)) else tr(w, k)
            return out
        if isinstance(v, list):
            if roditelj == 'zadnje':
                return [[r[0], M.get(r[1], r[1])] + r[2:] if isinstance(r, list) and len(r) > 1 else r for r in v]
            return [tr(w, roditelj) for w in v]
        return v
    return tr(x)


def ponuda_dana(tabla, K):
    """Za svaku utakmicu koja nije počela: svi igrači u ponudi, po stavci, na najčešćoj glavnoj granici:
    očekivanje, očekivani minuti, prosek sezone i poslednjih 5, strana na koju naginje (kalibrisano), najbolje kvote
    i do 3 razloga za tu stranu i 2 protiv. Ishod se dopisuje posle utakmice."""
    out = {}
    for u in tabla['utakmice']:
        if u['pocela']:
            continue
        L = []
        for st in u['strane']:
            tudja = next(x for x in u['strane'] if x is not st)
            for i in st['igraci']:
                if i['ne_igra']:
                    continue
                for s in 'PSA':
                    x = i['s'][s]
                    ng = naginje(x)
                    if not ng:
                        continue
                    na = [z for z in x['linije'] if z.get('m', 1) and z['l'] == ng['l']]
                    za, protiv = OB.analiza(i, s, ng, u, st, tudja, K, 3, protiv=2) if K else ([], [])
                    p5 = (x.get('posl') or [])[-5:]
                    pr = x.get('pred')
                    L.append(dict(k=i['k'], ime=i['ime'], tim=st['tim'], pos=i['pos'], s=s, l=ng['l'], strana=ng['strana'], pp=ng['pp'],
                                  neodl=ng['neodl'], pm=ng['pm'], fer=ng['fer'],
                                  mu=x['mu'], q=x['q'], min=i['min'], pros=x['pros'], p5=round(sum(p5) / len(p5), 1) if p5 else None,
                                  u=max(z['u'] for z in na), o=max(z['o'] for z in na), knjiga=len(na),
                                  pred=(pr['strana'] if pr else None), za=za, protiv=protiv))
        out[u['g']] = L
    return out


def igraci_kola(kolo):
    """Svi igrači tekućeg kola za karticu „Igrači“ (sažeto iz table): očekivano, raspon, forma, protivnik, glavne granice."""
    put = os.path.join(PROCENE, 'tabla', f'kolo{kolo}.json') if kolo else None
    if not put or not os.path.exists(put):
        return None
    t = ucitaj(put)
    B = Baza()
    from zajedno import utakmice as sve_ut
    domacin = {x['g']: x['dom'] for x in sve_ut()}
    K = OB.Kontekst(B, domacin)
    from zajedno import rokovi
    R = rokovi()
    sad_bg = dt.datetime.now(dt.timezone.utc).astimezone(BG)
    ut, out = [], []
    pk = os.path.join(PROCENE, 'predlozi', f'kolo{kolo}.json')
    obj_L = ucitaj(pk).get('predlozi', []) if os.path.exists(pk) else []
    objavljeni = {(p['k'], p['s'], p['dan']) for p in obj_L}
    primeni_spoj(t, obj_L)
    for u in t['utakmice']:
        # pre objave (12:00 na dan utakmice) nema procena: samo prosek, poslednje utakmice i granice kladionica
        skr = u['g'] in R and sad_bg < R[u['g']][0]
        ut.append(dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'],
                       objava=R[u['g']][0].isoformat() if u['g'] in R else None, skriveno=skr))
        for st in u['strane']:
            tudja = next(x for x in u['strane'] if x is not st)
            for i in st['igraci']:
                s_ = {}
                for s in 'PSA':
                    x = i['s'][s]
                    if skr:
                        s_[s] = dict(ng=None, mu=None, q=None, pros=x['pros'], posl=x['posl'], of=x['of'], vatra=x.get('vatra'),
                                     lin=[[z['kl'], z['l'], z['u'], z['o']] for z in x['linije'] if z.get('m', 1)], pred=None)
                        continue
                    pr = x.get('pred')
                    ng = None if i['ne_igra'] else naginje(x)
                    if ng:
                        ng['zasto'], ng['protiv'] = OB.analiza(i, s, ng, u, st, tudja, K, broj_tacaka(ng['pp']) - 1, protiv=3)
                    s_[s] = dict(ng=ng, mu=x['mu'], q=x['q'], pros=x['pros'], posl=x['posl'], of=x['of'], vatra=x.get('vatra'),
                                 lin=[[z['kl'], z['l'], z['u'], z['o'], round(z['pc'], 3)] for z in x['linije'] if z.get('m', 1)],
                                 pred=(dict(strana=pr['strana'], l=pr['l'], kl=pr['kl'], nivo=pr['nivo'], pp=pr['pp'])
                                       if pr and (i['k'], s, u['dan']) in objavljeni else None))
                zad = [[r['dan'][8:10] + '.' + r['dan'][5:7] + '.', r['opp'], round(r['min']), r['P'], r['S'], r['A']]
                       for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']][-5:][::-1]
                gs = [r for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']]
                n_ = len(gs)
                sez = dict(n=n_, min=round(sum(r['min'] for r in gs) / n_, 1), **{s: round(sum(r[s] for r in gs) / n_, 1) for s in 'PSA'},
                           mx={s: max(r[s] for r in gs) for s in 'PSA'}, mn={s: min(r[s] for r in gs) for s in 'PSA'}) if n_ else None
                out.append(dict(k=i['k'], zadnje=zad, sez=sez, ime=i['ime'], tim=st['tim'], prot=st['prot'], g=u['g'], pos=i['pos'], min=(sez['min'] if skr and sez else i['min']), n=i['n'],
                                posl_min=i['posl_min'], odsutan=i['odsutan'], ne_igra=i['ne_igra'], razlog=i.get('razlog'), upitan=i.get('upitan'), s=s_,
                                skriveno=skr or None))
    return dict(kolo=kolo, napravljeno=t['napravljeno'], podaci_do=t['podaci_do'], utakmice=ut, igraci=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    model.ucitaj_parametre()
    sp = ucitaj(os.path.join(PROCENE, 'spajanje.json'))
    folder = os.path.join(PROCENE, 'predlozi')
    os.makedirs(folder, exist_ok=True)
    sada = dt.datetime.now(dt.timezone.utc).astimezone(BG).strftime('%d.%m.%Y. %H:%M')
    if a.kolo:
        tabla = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
        put = os.path.join(folder, f'kolo{a.kolo}.json')
        st = ucitaj(put) if os.path.exists(put) else {'kolo': a.kolo, 'predlozi': []}
        # Objava i konačni predlozi (zajedno.rokovi): za utakmicu nema javnih procena pre 12:00 na dan utakmice.
        # Konačni predlozi su oni koji su objavljeni u trenutku roka (sat ili sat i po pre prve utakmice dana);
        # prvo osvežavanje posle roka ih samo zaključa. Ako do roka ništa nije objavljeno, prvo osvežavanje posle roka
        # daje konačne predloge. Utakmica koja počne bez konačnih predloga zaključava se sa poslednjim predlozima.
        from zajedno import utakmice as sve_ut, rokovi
        R = rokovi()
        sad_bg = dt.datetime.now(dt.timezone.utc).astimezone(BG)
        fmt = lambda x: x.strftime('%d.%m.%Y. %H:%M')
        konacno = st.setdefault('konacno', {})
        pocele = {u['g'] for u in tabla['utakmice'] if u['pocela']}
        objavljive = {u['g'] for u in tabla['utakmice'] if u['g'] in R and sad_bg >= R[u['g']][0]}
        for u in tabla['utakmice']:
            g = u['g']
            # od 6.11.2026: posle roka se zaključava svaka objavljena utakmica, i ona bez predloga (inače bi naknadno
            # pokretanje dopunilo predloge koji nisu bili na listi u trenutku roka)
            if str(g) not in konacno and g not in pocele and g in R and sad_bg >= R[g][1] and g in objavljive:
                konacno[str(g)] = fmt(R[g][1])
        zamrznute = pocele | {int(g) for g in konacno}
        zadrzi = [p for p in st['predlozi'] if p['g'] in zamrznute]          # zaključani
        K_ob = OB.Kontekst(Baza(), {x['g']: x['dom'] for x in sve_ut()})
        novi = [p for p in izaberi(tabla, K_ob) if p['g'] not in zamrznute and p['g'] in objavljive]
        # dan sa više utakmica: najbolji za ceo dan (izbor_dana); dan sa jednom utakmicom: svi predlozi te utakmice
        ut_dana = collections.Counter(u['dan'] for u in tabla['utakmice'])
        po_danu = collections.defaultdict(list)
        for p in novi:
            po_danu[p['dan']].append(p)
        B_dan = Baza()
        ranije = [(p['k'], p['s'], p['strana'], p['l']) for p in st['predlozi'] if p['g'] not in zamrznute]
        novi = [q for d, L in po_danu.items() for q in izbor_dana(L, B_dan, ranije)]
        # predlozi po spoju: tabla u memoriji dobija isti prikaz (strana, očekivanje), pa se obrazloženje piše nad tim
        idx = {(u['g'], i['k']): (u, st_i, i) for u in tabla['utakmice'] for st_i in u['strane'] for i in st_i['igraci']}
        primeni_spoj(tabla, zadrzi + novi)
        for p in novi:
            if p.get('spoj') and (p['g'], p['k']) in idx:
                u, st_i, i = idx[(p['g'], p['k'])]
                tudja = next(x for x in u['strane'] if x is not st_i)
                p['analiza'] = OB.analiza(i, p['s'], i['s'][p['s']]['pred'], u, st_i, tudja, K_ob, broj_tacaka(p['pp']))
        for d, L in IZBACENI_MM.items():         # dnevnik za proveru slaganja (spoj/provera.py)
            dput = os.path.join(PROCENE, '..', 'spoj', 'dnevnik', f'izbaceni_{d}.json')
            os.makedirs(os.path.dirname(dput), exist_ok=True)
            sacuvaj(dput, {'dan': d, 'upisano': sada, 'izbaceni': L})
        sada_konacno = [u['g'] for u in tabla['utakmice'] if u['g'] not in zamrznute and u['g'] in objavljive
                        and sad_bg >= R[u['g']][1] and u['snimci']]
        # promene u odnosu na prethodno osvežavanje (važe do početka utakmice)
        pre = {(p['g'], p['k']): p for p in st['predlozi'] if p['g'] not in zamrznute}
        g_pre = {p['g'] for p in pre.values()}
        opis = lambda p: f"{ {'P': 'poeni', 'S': 'skokovi', 'A': 'asist.'}[p['s']]} {'preko' if p['strana'] == 'o' else 'ispod'} {zr(p['l'])} · {zr(p['kvota'], 2)} {IME_KL.get(p['kl'], p['kl'])}"
        for p in novi:
            p['upisano'] = sada
            q = pre.get((p['g'], p['k']))
            if q:
                p['prvi_put'] = q.get('prvi_put') or q.get('upisano')
                if (q['s'], q['strana'], q['l']) != (p['s'], p['strana'], p['l']) or abs(q['kvota'] - p['kvota']) > 0.035:
                    p['promena'], p['ranije'], p['promena_u'] = 'izmenjeno', opis(q), sada
                elif q.get('promena'):
                    p['promena'], p['ranije'], p['promena_u'] = q['promena'], q.get('ranije'), q.get('promena_u')
            else:
                p['prvi_put'] = sada
                if p['g'] in g_pre:
                    p['promena'], p['promena_u'] = 'novo', sada
        # povučeni i izmenjeni predlozi (istorija u toku dana): ceo predlog, kada je objavljen i kada povučen;
        # ishod se upisuje kao i za predloge, ali se ne računa u učinak
        isti = lambda x: (x['g'], x['k'], x['s'], x['strana'], x['l'])
        nove_isti = {isti(p) for p in novi}
        uklonjeni = [x for x in st.get('uklonjeni', []) if x['g'] in zamrznute or ('s' in x and isti(x) not in nove_isti)
                     or ('s' not in x and (x['g'], x['k']) not in {(p['g'], p['k']) for p in novi})]
        nove_po_k = {(p['g'], p['k']): p for p in novi}
        for kk, q in pre.items():
            n = nove_po_k.get(kk)
            if n and isti(n) == isti(q):
                continue
            uklonjeni = [x for x in uklonjeni if not ('s' in x and isti(x) == isti(q))]
            uklonjeni.append(dict(g=q['g'], k=q['k'], ime=q['ime'], tim=q['tim'], prot=q.get('prot'), s=q['s'], strana=q['strana'],
                                  l=q['l'], kl=q['kl'], kvota=q['kvota'], pp=q.get('pp'), nivo=q.get('nivo'), mu=q.get('mu'),
                                  opis=opis(q), od=q.get('prvi_put') or q.get('upisano'), u=sada,
                                  vrsta='izmenjen' if n else 'povučen', zamena=opis(n) if n else None))
        st['uklonjeni'] = uklonjeni
        st['predlozi'] = zadrzi + novi
        for g in sada_konacno:
            konacno[str(g)] = sada
        # cela ponuda dana (arhiva za Istoriju): svi igrači u ponudi sa očekivanjem, stranom na koju naginju i razlozima;
        # osvežava se dok utakmica nije zaključana (isti trenutak kao konačni predlozi)
        ponuda = st.setdefault('ponuda', {})
        objav = {(p['g'], p['k'], p['s']) for p in st['predlozi']}
        for g, L in ponuda_dana(tabla, K_ob).items():
            for x in L:                      # od 6.11.2026: „predlog“ samo za objavljene predloge dana
                if (g, x['k'], x['s']) not in objav:
                    x['pred'] = None
            if g in objavljive and (g not in zamrznute or (str(g) not in ponuda and g not in pocele) or g in sada_konacno):
                ponuda[str(g)] = L
        st['osvezeno'] = sada
        pocetak = {x['g']: x['utc'].isoformat() for x in sve_ut()}
        st['utakmice'] = [dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'], pocela=u['pocela'],
                               pocetak=pocetak.get(u['g']), sastav=u.get('sastav'),
                               objava=R[u['g']][0].isoformat() if u['g'] in R else None,
                               rok=R[u['g']][1].isoformat() if u['g'] in R else None,
                               ponude=sorted(u['snimci'].keys()), snimci=u['snimci']) for u in tabla['utakmice']]
        # zatvaranje kvota (interno, za CLV): dok utakmica ne počne, za svaki predlog se pamti poslednja kvota iste
        # kladionice na istoj granici; posle početka ostaje kvota iz poslednjeg snimka pre utakmice
        lin = {}
        for u in tabla['utakmice']:
            if u['pocela']:
                continue
            for st_i in u['strane']:
                for i in st_i['igraci']:
                    for s in 'PSA':
                        for z in i['s'][s]['linije']:
                            if z.get('m', 1):
                                lin[(u['g'], i['k'], s, z['kl'], z['l'])] = z
        for p in st['predlozi']:
            z = lin.get((p['g'], p['k'], p['s'], p['kl'], p['l']))
            if z:
                p['zatv'] = z['o'] if p['strana'] == 'o' else z['u']
                p['zatv_fer'] = round(1 / (z['pc'] if p['strana'] == 'o' else 1 - z['pc']), 3)
        sacuvaj(put, st)
        pass  # collections je uvezen na vrhu
        if sada_konacno:
            print(f'kolo {a.kolo}: KONAČNI predlozi za utakmice {sada_konacno}')
        print(f'kolo {a.kolo}: predloga {len(st["predlozi"])} (zaključanih {len(zadrzi)}, novih {len(novi)}: '
              f'plus {sum(p["strana"] == "o" for p in novi)}, minus {sum(p["strana"] == "u" for p in novi)}; '
              f'nivoi {dict(collections.Counter(p["nivo"] for p in novi))})')

    # ishodi za sva kola
    B = Baza()
    ish = {(r['g'], r['k']): r for r in B.rows}
    igrane = {r['g'] for r in B.rows}
    kola = []
    for f in sorted(glob.glob(os.path.join(folder, 'kolo*.json')), key=lambda x: int(''.join(c for c in os.path.basename(x) if c.isdigit()))):
        st = ucitaj(f)
        for p in st['predlozi']:
            r = ish.get((p['g'], p['k']))
            if r:
                y = r[p['s']]
                p['ishod'] = y
                p['prosao'] = (y > p['l']) if p.get('strana') == 'o' else (y < p['l'])
            elif p['g'] in igrane:
                p['ishod'] = None; p['prosao'] = None; p['nije_igrao'] = True   # ulog se vraća
        for x in st.get('uklonjeni', []):
            if 's' not in x:
                continue
            r = ish.get((x['g'], x['k']))
            if r:
                x['ishod'] = r[x['s']]
                x['prosao'] = (r[x['s']] > x['l']) if x['strana'] == 'o' else (r[x['s']] < x['l'])
            elif x['g'] in igrane:
                x['ishod'] = None; x['prosao'] = None; x['nije_igrao'] = True
        for g, L in st.get('ponuda', {}).items():
            for x in L:
                r = ish.get((int(g), x['k']))
                if r:
                    x['ishod'], x['min_st'] = r[x['s']], round(r['min'])
                    x['prosao'] = (r[x['s']] > x['l']) if x['strana'] == 'o' else (r[x['s']] < x['l'])
                elif int(g) in igrane:
                    x['ishod'] = None; x['prosao'] = None; x['nije_igrao'] = True
        sacuvaj(f, st)
        kola.append(st)

    from zajedno import utakmice
    sad = dt.datetime.now(dt.timezone.utc)
    buduce = sorted([u for u in utakmice() if u['utc'] > sad - dt.timedelta(hours=3)], key=lambda u: u['utc'])
    tekuce = buduce[0]['r'] if buduce else None
    # na javnu stranicu ne idu provera unazad ni pragovi po strani (to je interna statistika)
    pr = sp['pravilo']
    javno_pr = dict(kvota_min=pr['kvota_min'], min_ut=pr['min_ut'], max_ut=pr['max_ut'], nivoi=pr['nivoi'])
    # zaključavanje delova stranice po paketu (za sada je sve otvoreno)
    # na javnu stranicu idu samo polja koja stranica koristi (bez internih verovatnoća, CLV i sl.)
    JAVNO = ('g', 'dan', 'vreme', 'k', 'ime', 'tim', 'prot', 's', 'strana', 'l', 'kl', 'kvota', 'pp', 'ev', 'nivo', 'rang', 'rang_dan', 'knjige', 'opseg',
             'q', 'mu', 'min', 'l0', 'vatra', 'pos', 'of', 'analiza', 'promena', 'ranije', 'promena_u', 'prvi_put', 'plus_iz', 'izostanci_tim', 'ishod', 'prosao', 'nije_igrao')
    # cela ponuda: razlozi samo za tekuće i prethodno kolo (veličina stranice); brojke za sva kola
    JAVNO_PON = ('k', 'ime', 'tim', 'pos', 's', 'l', 'strana', 'pp', 'mu', 'q', 'min', 'pros', 'p5', 'u', 'o', 'pred',
                 'ishod', 'min_st', 'prosao', 'nije_igrao')
    sa_razlozima = {k['kolo'] for k in kola if tekuce and k['kolo'] >= tekuce - 1}
    def pon_j(k):
        T = JAVNO_PON + (('za', 'protiv') if k['kolo'] in sa_razlozima else ())
        return {g: [{x: e[x] for x in T if x in e} for e in L] for g, L in k.get('ponuda', {}).items()}
    kola_j = [dict(kolo=k['kolo'], osvezeno=k.get('osvezeno'), konacno=k.get('konacno', {}), utakmice=k.get('utakmice', []),
                   uklonjeni=k.get('uklonjeni', []), ponuda=pon_j(k),
                   predlozi=[{x: p[x] for x in JAVNO if x in p} for p in k['predlozi']]) for k in kola]
    # CLV (interno): prosečna razlika naše kvote i zatvaranja
    for k in kola:
        Z = [p for p in k['predlozi'] if p.get('zatv') and p['g'] in {u['g'] for u in k.get('utakmice', []) if u.get('pocela')}]
        if Z:
            print(f"kolo {k['kolo']}: CLV {sum(p['kvota'] / p['zatv'] - 1 for p in Z) / len(Z):+.1%} prema zatvaranju iste kladionice, "
                  f"{sum(p['kvota'] / p['zatv_fer'] - 1 for p in Z if p.get('zatv_fer')) / len(Z):+.1%} prema fer kvoti ({len(Z)} predloga)")
    stat_p = os.path.join(PROCENE, 'podaci', 'statistika.json')
    stranica = dict(zakljucano=dict(napredno=False), osvezeno=sada, pravilo=javno_pr, kladionice=IME_KL, kola=kola_j, tekuce=tekuce,
                    igraci=igraci_kola(tekuce), statistika=ucitaj(stat_p) if os.path.exists(stat_p) else None)
    stranica = javni_kodovi(stranica)
    sab = open(os.path.join(PROCENE, 'javno', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(stranica, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'javno', 'predlozi.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    print('stranica: procene/javno/predlozi.html, kola', [k['kolo'] for k in kola])


if __name__ == '__main__':
    main()
