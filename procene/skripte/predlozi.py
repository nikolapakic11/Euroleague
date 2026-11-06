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
from model import Baza
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


def izaberi(tabla, K=None):
    """Predlozi su već izabrani u tabli (tabla.py, pravilo spajanje.izbor_utakmice); ovde se samo prepisuju, uz analizu."""
    out = []
    for u in tabla['utakmice']:
        if u['pocela']:
            continue
        for st in u['strane']:
            tudja = next(x for x in u['strane'] if x is not st)
            for i in st['igraci']:
                for s in 'PSA':
                    pr = i['s'][s].get('pred')
                    if not pr:
                        continue
                    z = next((z for z in i['s'][s]['linije'] if z['kl'] == pr['kl'] and z['l'] == pr['l']), {})
                    an = OB.analiza(i, s, pr, u, st, tudja, K, broj_tacaka(pr['pp'])) if K else []
                    out.append(dict(g=u['g'], dan=u['dan'], vreme=u['vreme'], k=i['k'], ime=i['ime'], tim=st['tim'], prot=st['prot'],
                                    s=s, strana=pr['strana'], l=pr['l'], kl=pr['kl'], kvota=pr['kvota'], pp=pr['pp'], ev=pr['ev'],
                                    nivo=pr['nivo'], rang=pr['rang'], fer=pr.get('fer'), ostale=pr.get('ostale', []), knjige=pr.get('knjige', []), soft=pr.get('soft'),
                                    opseg=pr.get('opseg', []), q=i['s'][s]['q'], mu=i['s'][s]['mu'], min=i['min'],
                                    pm=z.get('pm'), tr=z.get('tr'), l0=z.get('l0'), vatra=i['s'][s].get('vatra'),
                                    pos=i['pos'], of=i['s'][s]['of'], analiza=an))
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
    P = sorted([p for p in P if p.get('nivo') != 'slab' and not van(p)], key=lambda p: -ocena(p))
    if B is not None:
        for p in P:
            p['forma'] = list(forma(B, p))
        P = [p for p in P if p['forma'][1] < 4 or p['forma'][0] / p['forma'][1] >= DAN_FORMA_MIN]

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
    for x in isk.get('dodati', {}).get(P[0]['dan'] if P else '', []):     # ručno dodati (Nikola)
        for p in P:
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
    objavljeni = {(p['k'], p['s'], p['dan']) for p in (ucitaj(pk).get('predlozi', []) if os.path.exists(pk) else [])}
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
             'q', 'mu', 'min', 'l0', 'vatra', 'pos', 'of', 'analiza', 'promena', 'ranije', 'promena_u', 'prvi_put', 'ishod', 'prosao', 'nije_igrao')
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
