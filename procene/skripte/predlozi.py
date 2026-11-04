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
from model import Baza
from zajedno import PROCENE, BG, ucitaj, sacuvaj
import spajanje

KONACNO = '16:30'      # od ovog vremena na dan utakmice osvežavanje daje konačne predloge
IME_KL = {'admiral': 'Admiral', 'maxbet': 'MaxBet', 'mozzart': 'Mozzart', 'soccerbet': 'Soccerbet'}


POZM = {'G': 'bekovima', 'F': 'krilima', 'C': 'centrima'}
POZ1 = {'G': 'bek', 'F': 'krilo', 'C': 'centar'}
SNA = {'P': 'poena', 'S': 'skokova', 'A': 'asistencija'}


def zr(x, d=1):
    """Broj u srpskom zapisu (zarez)."""
    s = f'{x:.{d}f}'.replace('.', ',')
    return s[:-2] if d == 1 and s.endswith(',0') else s


def broj_tacaka(pp):
    """Koliko tačaka analize: jači izgledi, više obrazloženja."""
    return 6 if pp >= 0.60 else 4 if pp >= 0.55 else 2


def stavke_analize(i, s, l, u, moja, tudja, B, domacin):
    """Sve tačke za igrača i stavku na granici l, svaka sa smerom: d=+1 ide u prilog preko, d=-1 u prilog ispod.
    Vraća listu (prioritet, d, tekst); tekst važi za tu stranu."""
    x = i['s'][s]
    g = [r for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']]
    sg = lambda v: (v > 0) - (v < 0)
    T = []
    if g:
        n = len(g)
        pros = sum(r[s] for r in g) / n
        n_o, n_u = sum(r[s] > l for r in g), sum(r[s] < l for r in g)
        d = sg(n_o - n_u) or sg(pros - l)
        if d:
            T.append((1, d, f"Sezona: {'preko' if d > 0 else 'ispod'} {zr(l)} u {n_o if d > 0 else n_u} od {n} utakmica, prosek {zr(pros)} {SNA[s]}."))
        if n >= 4:
            l3 = [r[s] for r in g[-3:]]
            a3 = sum(l3) / 3
            if abs(a3 - pros) >= max(1.0, 0.15 * pros):
                T.append((4, sg(a3 - pros), f"Forma: poslednje 3 utakmice {', '.join(str(v) for v in l3)}, {'iznad' if a3 > pros else 'ispod'} proseka."))
        je_kuca = u['dom'] == moja['tim']
        kuca = [r[s] for r in g if domacin.get(r['g']) == r['team']]
        gost = [r[s] for r in g if domacin.get(r['g']) and domacin.get(r['g']) != r['team']]
        if len(kuca) >= 2 and len(gost) >= 2:
            ak, ag = sum(kuca) / len(kuca), sum(gost) / len(gost)
            ova, druga = (ak, ag) if je_kuca else (ag, ak)
            if abs(ak - ag) >= max(1.0, 0.2 * max(ak, ag)):
                gde, gde2 = ('Kod kuće', 'u gostima') if je_kuca else ('U gostima', 'kod kuće')
                T.append((6, sg(ova - druga), f"{gde} ima {'više' if ova > druga else 'manje'}: {zr(ova)} naspram {zr(druga)} {gde2}; ova utakmica je {gde.lower()}."))
        isti = [r for r in g if r['opp'] == moja['prot']]
        if isti and (all(r[s] > l for r in isti) or all(r[s] < l for r in isti)):
            T.append((7, 1 if isti[0][s] > l else -1, f"Protiv {moja['prot']} ove sezone: " + ', '.join(f"{r[s]} ({r['dan'][8:10]}.{r['dan'][5:7]}.)" for r in isti[-2:]) + '.'))
    pm = i.get('posl_min') or []
    if len(pm) >= 3:
        m3 = sum(pm[-3:]) / 3
        if abs(m3 - i['min']) >= 3:
            T.append((5, sg(m3 - i['min']), f"Minuti: u poslednje vreme igra {'više' if m3 > i['min'] else 'manje'} ({', '.join(str(m) for m in pm[-3:])} min, prosek {zr(i['min'])})."))
    of = x.get('of')
    b_of = model.PAR.get('B_OF', {}).get(s, 0.5)
    if of is not None and b_of > 0:                 # za stavku za koju model ne koristi odbranu protivnika, ne navodi se
        p = round((of - 1) * 100)
        if abs(p) >= 5:
            van = {j['k'] for j in tudja.get('nedostaju', [])}
            na_poz = sorted([j for j in tudja['igraci'] if j['pos'] == i['pos'] and not j['ne_igra'] and not j['odsutan'] and j['min'] >= 12 and j['k'] not in van],
                            key=lambda j: -j['min'])[:2]
            dod = f"; na poziciji {'su' if len(na_poz) > 1 else 'je'} {' i '.join(j['ime'] for j in na_poz)}" if na_poz else ''
            T.append((2, sg(p), f"Odbrana: {moja['prot']} dozvoljava {POZM.get(i['pos'], 'igračima na ovoj poziciji')} {abs(p)}% {'više' if p > 0 else 'manje'} {SNA[s]} od proseka lige{dod}."))
    tp = i.get('tempo')
    if tp and abs(tp ** model.PAR.get('B_TEMPO', {}).get(s, 0.5) - 1) >= 0.02:
        T.append((8, sg(tp - 1), f"Tempo: očekuje se {'brža' if tp > 1 else 'sporija'} utakmica od proseka lige ({'+' if tp > 1 else '−'}{abs(round((tp - 1) * 100))}% poseda)."))
    # verovatno odsutni rotacioni saigrači (tabla.py: nisu u sastavu ili ih nema ni kod jedne kladionice):
    # model to ne vidi, pa ostaje više minuta i lopti za ostale; za MINUS je to razlog protiv, za PLUS razlog za
    ned = [j for j in moja.get('nedostaju', []) if j['k'] != i['k']]
    if ned:
        T.append((2, 1, f"Nedostaju: kod {moja['tim']} verovatno ne {'igraju' if len(ned) > 1 else 'igra'} "
                        + ', '.join(f"{j['ime']} ({zr(j['min'])} min)" for j in ned[:3])
                        + ' (' + ('nisu u ponudi kladionica' if all(j['zasto'] != 'nije u sastavu' for j in ned) else 'van sastava ili van ponude') + ')'
                        + '; ostaje više minuta i lopti, a model računa sa prosekom sezone.'))
    ned2 = [j for j in tudja.get('nedostaju', []) if j['pos'] == i['pos']]
    if ned2:
        T.append((7, 1, f"Kod {tudja['tim']} na njegovoj poziciji verovatno ne {'igraju' if len(ned2) > 1 else 'igra'} {' i '.join(j['ime'] for j in ned2[:2])}."))
    raz = x['mu'] - l
    if abs(raz) >= 0.3:
        T.append((99, sg(raz), f"Granica {zr(l)} je {zr(abs(raz))} {'ispod' if raz > 0 else 'iznad'} našeg očekivanja ({zr(x['mu'])})."))
    return sorted(T)


def analiza(i, s, pr, u, moja, tudja, B, domacin, najvise=6, protiv=0):
    """Tačke koje idu u prilog izabranoj strani (najviše `najvise`, poslednja je razlika granice i očekivanja).
    Sa protiv>0 vraća (za, protiv): i do `protiv` tačaka koje govore protiv."""
    smer = 1 if pr['strana'] == 'o' else -1
    T = stavke_analize(i, s, pr['l'], u, moja, tudja, B, domacin)
    za = [t for p, d, t in T if d == smer and p < 99][:max(1, najvise - 1)] + [t for p, d, t in T if d == smer and p == 99]
    if not protiv:
        return za
    return za, [t for p, d, t in T if d == -smer][:protiv]


def naginje(x):
    """Strana na koju naginje igrač u stavci, na najčešćoj glavnoj granici: dict(strana, l, pp, knjige) ili None."""
    L = [z for z in x['linije'] if z.get('m', 1)]
    if not L:
        return None
    c = collections.Counter(z['l'] for z in L)
    l = sorted(c, key=lambda v: (-c[v], v))[0]
    pc = sum(z['pc'] for z in L if z['l'] == l) / c[l]
    return dict(strana='o' if pc >= 0.5 else 'u', l=l, pp=round(max(pc, 1 - pc), 3))


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
                    an = analiza(i, s, pr, u, st, tudja, B, domacin or {}, broj_tacaka(pr['pp'])) if B else []
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
    from zajedno import utakmice as sve_ut
    domacin = {x['g']: x['dom'] for x in sve_ut()}
    ut, out = [], []
    for u in t['utakmice']:
        ut.append(dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan']))
        for st in u['strane']:
            tudja = next(x for x in u['strane'] if x is not st)
            for i in st['igraci']:
                s_ = {}
                for s in 'PSA':
                    x = i['s'][s]
                    pr = x.get('pred')
                    ng = None if i['ne_igra'] else naginje(x)
                    if ng:
                        ng['zasto'], ng['protiv'] = analiza(i, s, ng, u, st, tudja, B, domacin, broj_tacaka(ng['pp']), protiv=3)
                    s_[s] = dict(ng=ng, mu=x['mu'], q=x['q'], pros=x['pros'], posl=x['posl'], of=x['of'], vatra=x.get('vatra'),
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
    model.ucitaj_parametre()
    sp = ucitaj(os.path.join(PROCENE, 'spajanje.json'))
    folder = os.path.join(PROCENE, 'predlozi')
    os.makedirs(folder, exist_ok=True)
    sada = dt.datetime.now(dt.timezone.utc).astimezone(BG).strftime('%d.%m.%Y. %H:%M')
    if a.kolo:
        tabla = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
        put = os.path.join(folder, f'kolo{a.kolo}.json')
        st = ucitaj(put) if os.path.exists(put) else {'kolo': a.kolo, 'predlozi': []}
        # Konačni predlozi: na dan utakmice od KONACNO (16:30) prvo osvežavanje daje konačne predloge (poslednja ponuda
        # i vesti o povredama); posle toga se za tu utakmicu ništa ne menja. Pre toga su predlozi preliminarni.
        # Utakmica koja počne pre konačnog osvežavanja zaključava se sa poslednjim predlozima.
        sad_bg = dt.datetime.now(dt.timezone.utc).astimezone(BG)
        konacno = st.setdefault('konacno', {})
        pocele = {u['g'] for u in tabla['utakmice'] if u['pocela']}
        zamrznute = pocele | {int(g) for g in konacno}
        zadrzi = [p for p in st['predlozi'] if p['g'] in zamrznute]          # zaključani
        from zajedno import utakmice as sve_ut
        novi = [p for p in izaberi(tabla, Baza(), {x['g']: x['dom'] for x in sve_ut()}) if p['g'] not in zamrznute]
        sada_konacno = [u['g'] for u in tabla['utakmice'] if u['g'] not in zamrznute and u['dan'] == sad_bg.date().isoformat()
                        and sad_bg.strftime('%H:%M') >= KONACNO and u['snimci']]
        # promene u odnosu na prethodno osvežavanje (važe do početka utakmice)
        pre = {(p['g'], p['k']): p for p in st['predlozi'] if p['g'] not in zamrznute}
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
        uklonjeni = [x for x in st.get('uklonjeni', []) if x['g'] in zamrznute or (x['g'], x['k']) not in nove_k]
        for kk, q in pre.items():
            if kk not in nove_k and not any((x['g'], x['k']) == kk for x in uklonjeni):
                uklonjeni.append(dict(g=q['g'], k=q['k'], ime=q['ime'], tim=q['tim'], opis=opis(q), u=sada))
        st['uklonjeni'] = uklonjeni
        st['predlozi'] = zadrzi + novi
        for g in sada_konacno:
            konacno[str(g)] = sada
        st['osvezeno'] = sada
        st['utakmice'] = [dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'], pocela=u['pocela'],
                               ponude=sorted(u['snimci'].keys()), snimci=u['snimci']) for u in tabla['utakmice']]
        sacuvaj(put, st)
        import collections
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
    stranica = dict(zakljucano=dict(napredno=False), osvezeno=sada, pravilo=javno_pr, kladionice=IME_KL, kola=kola, tekuce=tekuce,
                    igraci=igraci_kola(tekuce))
    sab = open(os.path.join(PROCENE, 'javno', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(stranica, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'javno', 'predlozi.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    print('stranica: procene/javno/predlozi.html, kola', [k['kolo'] for k in kola])


if __name__ == '__main__':
    main()
