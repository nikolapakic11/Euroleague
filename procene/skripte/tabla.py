"""Tabla procena za jedno kolo.

  python3 procene/skripte/tabla.py --kolo 11 [--dnevnik]

Za svaku utakmicu kola i svakog igrača koji je igrao ove sezone:
  očekivano i raspon za P, S, A; ponude svih kladionica za dan utakmice (poslednji snimak),
  verovatnoća za preko i ispod na svakoj granici, najbolja cena i razilaženja granica.
Minuti su prosek ove sezone (model.PAR['MINUTI']). Igrač koji nije u objavljenom sastavu (sastavi.py) ne igra. Izuzeci (povreda, „ne igra“) samo kroz procene/minuti.json, npr.
  {"11": {"nikola milutinov": 0, "facundo campazzo": 22}}
Izlaz: procene/tabla/kolo<N>.json (podaci) i procene/tabla/kolo<N>.html (stranica table, iz sablon.html).
--dnevnik: upisuje procene za utakmice koje još nisu počele u procene/dnevnik/kolo<N>.json;
           procena se osvežava do početka utakmice, posle toga ostaje zaključana.
"""
import argparse, collections, datetime as dt, glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import model
from model import Baza, verovatnoca_preko, percentili, raspodela
from zajedno import kljuc_snimka, BAZA, PROCENE, BG, ucitaj, sacuvaj, tim, utakmice, pn
import spajanje

KLADIONICE = ('admiral', 'maxbet', 'mozzart', 'soccerbet')
IME_KL = {'admiral': 'Admiral', 'maxbet': 'MaxBet', 'mozzart': 'Mozzart', 'soccerbet': 'Soccerbet'}
MESECI = re.compile(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})')


def dan_ponude(p, rezerva):
    m = MESECI.search(p.get('time') or '')
    if m:
        return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{4}-\d{2}-\d{2})', p.get('time') or '')
    return m.group(1) if m else rezerva


def ponude_za_dane(dani):
    """{(kladionica, dan): (snimak_vreme, [picks], [picks prvog snimka tog dana])} — poslednji snimak koji sadrži taj dan."""
    out = {}
    for kl in KLADIONICE:
        for f in sorted(glob.glob(os.path.join(BAZA, 'ponude', kl, '*.json')), key=kljuc_snimka):
            ime = os.path.basename(f)
            md = re.search(r'\d{4}-\d{2}-\d{2}', ime)      # npr. 2026-11-04_a.json ili mozzart_2026-11-04_1630.json
            if not md:
                continue
            ime = ime[md.start():]
            j = ucitaj(f)
            if 'picks' not in j:
                continue
            po = collections.defaultdict(list)
            for p in j['picks']:
                po[dan_ponude(p, ime[:10])].append(p)
            for d, lst in po.items():
                if d in dani:
                    prvi = out[(kl, d)][2] if (kl, d) in out else lst
                    out[(kl, d)] = (j.get('at'), lst, prvi)
            # lestvice „N+“ (Soccerbet): [igrač, tim, stavka, N, kvota], važe za dan snimka
            if j.get('x') and ime[:10] in dani:
                LESTVICE[(kl, ime[:10])] = j['x']
    return out


LESTVICE = {}


def soft_spot(i, s, strana, pred, sp_w):
    """Sve ponuđene granice za stranu predloga (glavne, alternativne, lestvice) sa verovatnoćom i najboljom kvotom,
    i „soft spot“: granica sa najvećim očekivanim povraćajem (verovatnoća × kvota − 1) među onima sa bar 50%."""
    x = i['s'][s]
    tacke = {}
    for z in x['linije']:
        kv = z['o'] if strana == 'o' else z['u']
        p = z['pc'] if strana == 'o' else 1 - z['pc']
        t = tacke.get(z['l'])
        if not t or kv > t['k']:
            tacke[z['l']] = dict(l=z['l'], k=kv, kl=z['kl'], p=round(p, 3), vrsta='granica')
    if strana == 'o':
        for z in x.get('lest', []):
            l = z['n'] - 0.5
            t = tacke.get(l)
            if not t or z['k'] > t['k']:
                tacke[l] = dict(l=l, k=z['k'], kl=z['kl'], p=round(z['pc'], 3), vrsta='lestvica', n=z['n'])
    T = sorted(tacke.values(), key=lambda t: t['l'])
    kand = [t for t in T if t['p'] >= 0.5 and t['k'] >= 1.2]
    soft = max(kand, key=lambda t: t['p'] * t['k']) if kand else None
    if soft:
        soft = dict(soft, ev=round(soft['p'] * soft['k'] - 1, 3),
                    isti=(soft['l'] == pred['l'] and soft['k'] <= pred['kvota'] + 1e-9))
    return T, soft


def rosteri():
    """kod tima -> {ključ igrača: (ime, pozicija)} za aktivne igrače."""
    out = {}
    for f in glob.glob(os.path.join(BAZA, 'rosteri', '*.json')):
        kod = os.path.basename(f)[:-5]
        out[kod] = {}
        for x in ucitaj(f):
            if x.get('type') == 'J' and x.get('person') and x.get('active', True):
                out[kod][pn(x['person']['name'])] = (x['person']['name'], x.get('positionName') or '')
    return out


VATRA_MIN = {'P': 4, 'S': 2, 'A': 1.5}


def vatra(g, s):
    """Igrač u formi u stavci s: poslednje 3 utakmice bar 30% i bar VATRA_MIN iznad proseka ranijih utakmica,
    i bar 2 od 3 iznad tog proseka; samo za igrače sa bar 15 minuta u proseku. Samo informacija: u oktobru nije sama predviđala ishod granica."""
    if len(g) < 4:
        return None
    l3, pre = g[-3:], g[:-3]
    a3 = sum(r[s] for r in l3) / 3
    ap = sum(r[s] for r in pre) / len(pre)
    if a3 >= 1.3 * ap and a3 - ap >= VATRA_MIN[s] and sum(r[s] > ap for r in l3) >= 2:
        return dict(l3=[r[s] for r in l3], a3=round(a3, 1), ap=round(ap, 1), pct=round((a3 / ap - 1) * 100) if ap else None)
    return None


def lepo_ime(n):
    if ',' in n:
        a, b = n.split(',', 1)
        return (b.strip().title() + ' ' + a.strip().title()).strip()
    return n.title()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int, required=True)
    ap.add_argument('--dnevnik', action='store_true')
    a = ap.parse_args()
    model.ucitaj_parametre()
    B = Baza()
    P = model.PAR
    sve = utakmice()
    kolo = sorted([u for u in sve if u['r'] == a.kolo], key=lambda u: u['utc'])
    if not kolo:
        sys.exit('nema utakmica za kolo %d' % a.kolo)
    ros = rosteri()
    rucno = {}
    rp = os.path.join(PROCENE, 'minuti.json')
    if os.path.exists(rp):
        rucno = ucitaj(rp).get(str(a.kolo), {})
    sp_put = os.path.join(PROCENE, 'spajanje.json')
    sp_j = ucitaj(sp_put) if os.path.exists(sp_put) else {}
    sp_w = sp_j.get('w')
    dani = {u['dan'] for u in kolo}
    pon = ponude_za_dane(dani)
    poslednji_dan = max(r['dan'] for r in B.rows)
    sp_sast = os.path.join(PROCENE, 'podaci', 'sastavi.json')
    sastavi = ucitaj(sp_sast) if os.path.exists(sp_sast) else {}
    sada = dt.datetime.now(dt.timezone.utc)

    # odigrane utakmice po timu (za „nije igrao poslednjih N“)
    tim_g = collections.defaultdict(list)
    for r in B.rows:
        if r['g'] not in tim_g[r['team']]:
            tim_g[r['team']].append(r['g'])

    utak = []
    for u in kolo:
        stranice = []
        for kod, prot in ((u['dom'], u['gost']), (u['gost'], u['dom'])):
            # igrači: odigrali bar jednu utakmicu ove sezone za ovaj tim, ili su na rosteru i imaju utakmice
            kljucevi = {r['k'] for r in B.rows if r['team'] == kod}
            kljucevi |= {k for k in ros.get(kod, {}) if k in B.byk}
            # ako je igrač prešao u drugi tim, ostaje samo u novom
            kljucevi = {k for k in kljucevi if B.byk[k][-1]['team'] == kod or k in ros.get(kod, {})}
            igraci = []
            poslednje3 = tim_g[kod][-3:]
            sastav = set((sastavi.get(str(u['g'])) or {}).get(kod) or [])
            for k in kljucevi:
                g = B.byk[k]
                ime = lepo_ime(ros.get(kod, {}).get(k, (g[-1]['name'], ''))[0])
                odsutan = sum(1 for gg in poslednje3 if not any(r['g'] == gg for r in g))
                rm = rucno.get(k)
                e = B.procena(k, u['dan'], kod, prot, minuti=(rm if rm not in (None, 0) else None))
                if not e:
                    continue
                st = {}
                for s in 'PSA':
                    x = e['s'][s]
                    q = percentili(x['mu'], x['var'])
                    # za stranicu: učinak po minutu sa kontekstom i rasipanje, da bi se minuti menjali na stranici
                    c_eff = P['C'][s] * (1 + P['CV'] * e['min_cv'])
                    st[s] = dict(mu=x['mu'], var=x['var'], q=q, rpm=round(x['mu'] / e['min'], 4) if e['min'] else 0,
                                 A=P['A'][s], C=round(c_eff, 4), of=x['of'], pros=x['pros'], posl=x['poslednje'], linije=[],
                                 vatra=vatra([r for r in g if r['dan'] < u['dan']], s) if e['min'] >= 15 else None)
                igraci.append(dict(k=k, ime=ime, pos=e['pos'], n=e['n'], min=e['min'], min_cv=e['min_cv'],
                                   posl_min=e['poslednji_min'], prosla=e['prosla'], odsutan=odsutan, tempo=e.get('tempo'),
                                   ne_igra=(rm == 0) or bool(sastav and k not in sastav),
                                   razlog=('nije u sastavu' if sastav and k not in sastav else 'ručno' if rm == 0 else None),
                                   rucno_min=rm if rm not in (None, 0) else None, s=st))
            igraci.sort(key=lambda x: -x['min'])
            stranice.append(dict(tim=kod, prot=prot, igraci=igraci))
        # ponude
        po_kljucu = {i['k']: (st_i, i) for st_i in stranice for i in st_i['igraci']}
        nepoznati = collections.Counter()
        snimci = {}
        for kl in KLADIONICE:
            if (kl, u['dan']) not in pon:
                continue
            at, picks, prvi = pon[(kl, u['dan'])]
            # glavne granice iz prvog snimka dana, za kretanje granice
            prve = {}
            for p in prvi:
                if p.get('m', 1) and p.get('s') in ('P', 'S', 'A'):
                    prve[(p['p'].lower(), p['s'])] = p['l']
            for p in picks:
                if p.get('s') not in ('P', 'S', 'A') or not p.get('u') or not p.get('o'):
                    continue
                k, kt = B.nadji_u_utakmici(p['p'], p.get('t'), p.get('tk'))
                if kt not in (u['dom'], u['gost']):
                    continue
                if k not in po_kljucu:
                    nepoznati[p['p']] += 1
                    continue
                snimci[kl] = at
                _, i = po_kljucu[k]
                x = i['s'][p['s']]
                pm = verovatnoca_preko(p['s'], x['mu'], x['var'], p['l'])
                tr = (1 / p['o']) / (1 / p['u'] + 1 / p['o'])
                pc = spajanje.preko(sp_w, p['s'], pm, tr) if sp_w else pm
                lin = dict(kl=kl, l=p['l'], u=p['u'], o=p['o'], m=p.get('m', 1), pm=round(pm, 4), tr=round(tr, 4), pc=round(pc, 4))
                l0 = prve.get((p['p'].lower(), p['s']))
                if p.get('m', 1) and l0 is not None and l0 != p['l']:
                    lin['l0'] = l0                     # granica se pomerila od prvog snimka dana
                x['linije'].append(lin)
        # lestvice „N+“ (samo preko): procena modela, a kvote bez marže približno (marža lestvica ~8%)
        for (kl, d), X in LESTVICE.items():
            if d != u['dan']:
                continue
            for igr, tm_ime, s_, n_, kv in X:
                if s_ not in ('P', 'S', 'A') or not kv or kv <= 1:
                    continue
                k, kt = B.nadji_u_utakmici(igr, tm_ime, None)
                if k not in po_kljucu or kt not in (u['dom'], u['gost']):
                    continue
                _, i = po_kljucu[k]
                x = i['s'][s_]
                pm = verovatnoca_preko(s_, x['mu'], x['var'], n_ - 0.5)
                tr_est = min(0.97, (1 / kv) / 1.08)
                pc = spajanje.preko(sp_w, s_, pm, tr_est) if sp_w else pm
                x.setdefault('lest', []).append(dict(kl=kl, n=n_, k=kv, pm=round(pm, 4), pc=round(pc, 4)))
        # predlozi za utakmicu: 4 do 6, po pravilu iz spajanje.izbor_utakmice (samo glavne granice)
        kand = []
        for st_i in stranice:
            for i in st_i['igraci']:
                if i['ne_igra'] or i['odsutan'] > 0 or i['n'] < 3:
                    continue
                for s in 'PSA':
                    for z in i['s'][s]['linije']:
                        if not z.get('m', 1):
                            continue
                        pc = z['pc']
                        for strana, pp, kv in (('o', pc, z['o']), ('u', 1 - pc, z['u'])):
                            kand.append(dict(igr=i['k'], s=s, strana=strana, pp=pp, ev=pp * kv - 1, k=kv, l=z['l'], kl=z['kl']))
        for c in (spajanje.izbor_utakmice(kand) if sp_w else []):
            _, i = po_kljucu[c['igr']]
            pred = dict(strana=c['strana'], pp=round(c['pp'], 3), ev=round(c['ev'], 3), kvota=c['k'], l=c['l'], kl=c['kl'],
                        nivo=c['nivo'], rang=c['rang'])
            # iste granice i strane kod ostalih kladionica
            pred['ostale'] = sorted([dict(kl=z['kl'], k=(z['o'] if c['strana'] == 'o' else z['u']))
                                     for z in i['s'][c['s']]['linije'] if z['l'] == c['l'] and z['kl'] != c['kl'] and z.get('m', 1)],
                                    key=lambda t: -t['k'])
            # sve kladionice: glavna granica i kvote za tu stavku (za poređenje na kartici predloga)
            red_kl = {k: n for n, k in enumerate(KLADIONICE)}
            pred['knjige'] = sorted([dict(kl=z['kl'], l=z['l'], u=z['u'], o=z['o']) for z in i['s'][c['s']]['linije'] if z.get('m', 1)],
                                    key=lambda t: red_kl.get(t['kl'], 9))
            T, soft = soft_spot(i, c['s'], c['strana'], pred, sp_w)
            pred['opseg'] = T
            pred['soft'] = soft
            i['s'][c['s']]['pred'] = pred
        # razilaženja: preko na nižoj granici kod jedne, ispod na višoj kod druge
        raz = []
        for st_i in stranice:
            for i in st_i['igraci']:
                for s in 'PSA':
                    L = [z for z in i['s'][s]['linije'] if z.get('m', 1)]   # samo glavne granice (Soccerbet nudi i ±2)
                    if len(L) < 2:
                        continue
                    nize = min(L, key=lambda z: (z['l'], -z['o']))
                    vise = max(L, key=lambda z: (z['l'], z['u']))
                    if vise['l'] - nize['l'] >= 1 and nize['kl'] != vise['kl']:
                        pm = raspodela(i['s'][s]['mu'], i['s'][s]['var'])
                        sred = sum(pm[int(math.floor(nize['l'])) + 1:int(math.floor(vise['l'])) + 1])
                        raz.append(dict(k=i['k'], ime=i['ime'], tim=st_i['tim'], s=s, preko=nize, ispod=vise,
                                        p_obe=round(sred, 3)))
        utak.append(dict(g=u['g'], dan=u['dan'], vreme=u['utc'].astimezone(BG).strftime('%d.%m. %H:%M'),
                         dom=u['dom'], gost=u['gost'], pocela=u['utc'] <= sada, strane=stranice, raz=raz,
                         sastav=(sastavi.get(str(u['g'])) or {}).get('at'),
                         snimci={IME_KL[k]: v for k, v in snimci.items()}, nepoznati=dict(nepoznati)))
    out = dict(kolo=a.kolo, napravljeno=sada.astimezone(BG).strftime('%d.%m.%Y. %H:%M'),
               podaci_do=poslednji_dan, parametri=P.get('_podeseno', ''), kal=P.get('KAL', {}), sp_w=sp_w, pravilo=sp_j.get('pravilo'), utakmice=utak,
               kladionice=[IME_KL[k] for k in KLADIONICE])
    put = os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json')
    sacuvaj(put, out, kompaktno=True)
    # stranica table: šablon + podaci
    sab = open(os.path.join(PROCENE, 'tabla', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(out, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    n_lin = sum(len(i['s'][s]['linije']) for u in utak for st in u['strane'] for i in st['igraci'] for s in 'PSA')
    print(f'kolo {a.kolo}: utakmica {len(utak)}, igrača {sum(len(st["igraci"]) for u in utak for st in u["strane"])}, '
          f'granica {n_lin}, podaci do {poslednji_dan}')
    for u in utak:
        if u['nepoznati']:
            print('  nepoznati u', u['dom'], u['gost'], u['nepoznati'])

    if a.dnevnik:
        dp = os.path.join(PROCENE, 'dnevnik', f'kolo{a.kolo}.json')
        dn = ucitaj(dp) if os.path.exists(dp) else {'kolo': a.kolo, 'stavke': []}
        nepocete = {u['g'] for u in utak if not u['pocela']}
        dn['stavke'] = [x for x in dn['stavke'] if x['g'] not in nepocete]
        vec = {(x['g'], x['k'], x['s']) for x in dn['stavke']}
        novo = 0
        for u in utak:
            if u['pocela']:
                continue
            for st in u['strane']:
                for i in st['igraci']:
                    if i['ne_igra']:
                        continue
                    for s in 'PSA':
                        if (u['g'], i['k'], s) in vec:
                            continue
                        x = i['s'][s]
                        dn['stavke'].append(dict(g=u['g'], dan=u['dan'], k=i['k'], ime=i['ime'], tim=st['tim'], s=s,
                                                 upisano=out['napravljeno'], podaci_do=poslednji_dan, min=i['min'],
                                                 mu=x['mu'], var=x['var'], q=x['q'],
                                                 linije=[dict(kl=z['kl'], l=z['l'], u=z['u'], o=z['o'], pm=z['pm'], tr=z['tr'], pc=z['pc']) for z in x['linije']]))
                        novo += 1
        sacuvaj(dp, dn, kompaktno=True)
        print('dnevnik: osveženih procena', novo, 'ukupno', len(dn['stavke']))


if __name__ == '__main__':
    main()
