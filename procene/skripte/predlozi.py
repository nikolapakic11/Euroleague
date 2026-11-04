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
import argparse, datetime as dt, glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
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


def analiza(i, s, pr, u, moja, tudja, B, domacin):
    """Kratke tačke zašto očekujemo to što očekujemo: minuti, sezona, forma, protivnik, ko je na poziciji, odsutni."""
    x = i['s'][s]
    g = [r for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']]
    o = pr['strana'] == 'o'
    l = pr['l']
    out = []
    # minuti
    pm = i.get('posl_min') or []
    m3 = sum(pm[-3:]) / len(pm[-3:]) if pm else None
    t = f"Minuti: {zr(i['min'])} u proseku"
    if pm:
        t += f", poslednje 3 utakmice {', '.join(str(m) for m in pm[-3:])}"
    if m3 is not None and m3 - i['min'] >= 3:
        t += '; u poslednje vreme igra više'
    elif m3 is not None and i['min'] - m3 >= 3:
        t += '; u poslednje vreme igra manje'
    out.append(t + '.')
    # sezona i granica
    if g:
        n = len(g)
        prolaz = sum((r[s] > l) if o else (r[s] < l) for r in g)
        out.append(f"Sezona: {zr(sum(r[s] for r in g) / n)} {SNA[s]} u {n} utakmica; {'preko' if o else 'ispod'} {zr(l)} u {prolaz} od {n}.")
        l3 = [r[s] for r in g[-3:]]
        a3 = sum(l3) / len(l3)
        pros = sum(r[s] for r in g) / n
        if n >= 4:
            ocena = 'iznad proseka' if a3 >= pros * 1.15 and a3 - pros >= 1 else 'ispod proseka' if a3 <= pros * 0.85 and pros - a3 >= 1 else 'blizu proseka'
            out.append(f"Forma: poslednje 3 utakmice {', '.join(str(v) for v in l3)}, {ocena}.")
        # dom i gost
        kuca = [r[s] for r in g if domacin.get(r['g']) == r['team']]
        gost = [r[s] for r in g if domacin.get(r['g']) and domacin.get(r['g']) != r['team']]
        if len(kuca) >= 2 and len(gost) >= 2:
            ak, ag = sum(kuca) / len(kuca), sum(gost) / len(gost)
            if abs(ak - ag) >= max(1.0, 0.2 * max(ak, ag)):
                je_kuca = u['dom'] == moja['tim']
                out.append(f"Kod kuće {zr(ak)}, u gostima {zr(ag)}; ova utakmica je {'kod kuće' if je_kuca else 'u gostima'}.")
        isti = [r for r in g if r['opp'] == moja['prot']]
        if isti:
            out.append(f"Protiv {moja['prot']} ove sezone: " + ', '.join(f"{r[s]} ({r['dan'][8:10]}.{r['dan'][5:7]}.)" for r in isti[-2:]) + '.')
    # protivnik
    of = x.get('of')
    if of is not None:
        p = round((of - 1) * 100)
        kome = POZM.get(i['pos'], 'igračima na ovoj poziciji')
        if abs(p) >= 5:
            out.append(f"Odbrana: {moja['prot']} dozvoljava {kome} {abs(p)}% {'više' if p > 0 else 'manje'} {SNA[s]} od proseka lige.")
        else:
            out.append(f"Odbrana: {moja['prot']} dozvoljava {kome} prosečan broj {SNA[s]}.")
    tp = i.get('tempo')
    if tp and abs(tp - 1) >= 0.03:
        out.append(f"Tempo: očekuje se {'brža' if tp > 1 else 'sporija'} utakmica od proseka lige ({'+' if tp > 1 else '−'}{abs(round((tp - 1) * 100))}% poseda).")
    # ko je na poziciji kod protivnika
    na_poz = [j for j in tudja['igraci'] if j['pos'] == i['pos'] and not j['ne_igra'] and not j['odsutan'] and j['min'] >= 12]
    na_poz.sort(key=lambda j: -j['min'])
    if na_poz:
        out.append(f"Na poziciji kod {moja['prot']}: " + ', '.join(f"{j['ime']} ({zr(j['min'])} min)" for j in na_poz[:2]) + '.')
    # odsutni: van sastava (potvrđeno) ili nisu igrali bar 2 od poslednje 3 utakmice
    def odsutni(st_):
        return [j['ime'] + (' (van sastava)' if j['ne_igra'] else '') for j in st_['igraci']
                if j['k'] != i['k'] and j['min'] >= 12 and (j['ne_igra'] or j['odsutan'] >= 2)][:2]
    d = [f"{x['tim']} {', '.join(L)}" for x in (moja, tudja) for L in [odsutni(x)] if L]
    if d:
        out.append('Nedostaju: ' + '; '.join(d) + '.')
    # zaključak
    mu = x['mu']
    raz = l - mu
    if abs(raz) >= 0.3:
        out.append(f"Granica {zr(l)} je {zr(abs(raz))} {'iznad' if raz > 0 else 'ispod'} našeg očekivanja ({zr(mu)}).")
    return out


def izaberi(tabla, B=None, domacin=None):
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
                    an = analiza(i, s, pr, u, st, tudja, B, domacin or {}) if B else []
                    out.append(dict(g=u['g'], dan=u['dan'], vreme=u['vreme'], k=i['k'], ime=i['ime'], tim=st['tim'], prot=st['prot'],
                                    s=s, strana=pr['strana'], l=pr['l'], kl=pr['kl'], kvota=pr['kvota'], pp=pr['pp'], ev=pr['ev'],
                                    nivo=pr['nivo'], rang=pr['rang'], ostale=pr.get('ostale', []), knjige=pr.get('knjige', []), soft=pr.get('soft'),
                                    opseg=pr.get('opseg', []), q=i['s'][s]['q'], mu=i['s'][s]['mu'], min=i['min'],
                                    pm=z.get('pm'), tr=z.get('tr'), l0=z.get('l0'), vatra=i['s'][s].get('vatra'),
                                    pos=i['pos'], of=i['s'][s]['of'], analiza=an))
    return out


def igraci_kola(kolo):
    """Svi igrači tekućeg kola za karticu „Igrači“ (sažeto iz table): očekivano, raspon, forma, protivnik, glavne granice."""
    put = os.path.join(PROCENE, 'tabla', f'kolo{kolo}.json') if kolo else None
    if not put or not os.path.exists(put):
        return None
    t = ucitaj(put)
    B = Baza()
    ut, out = [], []
    for u in t['utakmice']:
        ut.append(dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme']))
        for st in u['strane']:
            for i in st['igraci']:
                s_ = {}
                for s in 'PSA':
                    x = i['s'][s]
                    pr = x.get('pred')
                    s_[s] = dict(mu=x['mu'], q=x['q'], pros=x['pros'], posl=x['posl'], of=x['of'], vatra=x.get('vatra'),
                                 lin=[[z['kl'], z['l'], z['u'], z['o'], round(z['pc'], 3)] for z in x['linije'] if z.get('m', 1)],
                                 pred=(dict(strana=pr['strana'], l=pr['l'], kl=pr['kl'], nivo=pr['nivo'], pp=pr['pp']) if pr else None))
                zad = [[r['dan'][8:10] + '.' + r['dan'][5:7] + '.', r['opp'], round(r['min']), r['P'], r['S'], r['A']]
                       for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']][-5:][::-1]
                gs = [r for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']]
                n_ = len(gs)
                sez = dict(n=n_, min=round(sum(r['min'] for r in gs) / n_, 1), **{s: round(sum(r[s] for r in gs) / n_, 1) for s in 'PSA'},
                           mx={s: max(r[s] for r in gs) for s in 'PSA'}, mn={s: min(r[s] for r in gs) for s in 'PSA'}) if n_ else None
                out.append(dict(k=i['k'], zadnje=zad, sez=sez, ime=i['ime'], tim=st['tim'], prot=st['prot'], g=u['g'], pos=i['pos'], min=i['min'], n=i['n'],
                                posl_min=i['posl_min'], odsutan=i['odsutan'], ne_igra=i['ne_igra'], razlog=i.get('razlog'), s=s_))
    return dict(kolo=kolo, napravljeno=t['napravljeno'], podaci_do=t['podaci_do'], utakmice=ut, igraci=out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    sp = ucitaj(os.path.join(PROCENE, 'spajanje.json'))
    folder = os.path.join(PROCENE, 'predlozi')
    os.makedirs(folder, exist_ok=True)
    sada = dt.datetime.now(dt.timezone.utc).astimezone(BG).strftime('%d.%m.%Y. %H:%M')
    if a.kolo:
        tabla = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
        put = os.path.join(folder, f'kolo{a.kolo}.json')
        st = ucitaj(put) if os.path.exists(put) else {'kolo': a.kolo, 'predlozi': []}
        pocele = {u['g'] for u in tabla['utakmice'] if u['pocela']}
        zadrzi = [p for p in st['predlozi'] if p['g'] in pocele]          # zaključani
        from zajedno import utakmice as sve_ut
        novi = izaberi(tabla, Baza(), {x['g']: x['dom'] for x in sve_ut()})
        # promene u odnosu na prethodno osvežavanje (važe do početka utakmice)
        pre = {(p['g'], p['k']): p for p in st['predlozi'] if p['g'] not in pocele}
        g_pre = {p['g'] for p in pre.values()}
        opis = lambda p: f"{ {'P': 'poeni', 'S': 'skokovi', 'A': 'asist.'}[p['s']]} {'preko' if p['strana'] == 'o' else 'ispod'} {p['l']:g} · {p['kvota']:.2f} {IME_KL.get(p['kl'], p['kl'])}"
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
        nove_k = {(p['g'], p['k']) for p in novi}
        uklonjeni = [x for x in st.get('uklonjeni', []) if x['g'] not in pocele and (x['g'], x['k']) not in nove_k]
        for kk, q in pre.items():
            if kk not in nove_k and not any((x['g'], x['k']) == kk for x in uklonjeni):
                uklonjeni.append(dict(g=q['g'], k=q['k'], ime=q['ime'], tim=q['tim'], opis=opis(q), u=sada))
        st['uklonjeni'] = uklonjeni
        st['predlozi'] = zadrzi + novi
        st['osvezeno'] = sada
        st['utakmice'] = [dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'], pocela=u['pocela'],
                               ponude=sorted(u['snimci'].keys()), snimci=u['snimci']) for u in tabla['utakmice']]
        sacuvaj(put, st)
        import collections
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
        sacuvaj(f, st)
        kola.append(st)

    from zajedno import utakmice
    sad = dt.datetime.now(dt.timezone.utc)
    buduce = sorted([u for u in utakmice() if u['utc'] > sad - dt.timedelta(hours=3)], key=lambda u: u['utc'])
    tekuce = buduce[0]['r'] if buduce else None
    # na javnu stranicu ne idu provera unazad ni pragovi po strani (to je interna statistika)
    pr = sp['pravilo']
    javno_pr = dict(kvota_min=pr['kvota_min'], min_ut=pr['min_ut'], max_ut=pr['max_ut'], nivoi=pr['nivoi'])
    stranica = dict(osvezeno=sada, pravilo=javno_pr, kladionice=IME_KL, kola=kola, tekuce=tekuce,
                    igraci=igraci_kola(tekuce))
    sab = open(os.path.join(PROCENE, 'javno', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(stranica, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'javno', 'predlozi.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    print('stranica: procene/javno/predlozi.html, kola', [k['kolo'] for k in kola])


if __name__ == '__main__':
    main()
