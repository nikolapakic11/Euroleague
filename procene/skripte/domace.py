"""Utakmice ekipa Evrolige van Evrolige (domaće lige i kupovi) i minuti igrača u njima. Samo prikupljanje, bez prikaza.

  python3 procene/skripte/domace.py              osveži timove, raspored i statistiku završenih utakmica
  python3 procene/skripte/domace.py --pregled    kratak pregled: domaće utakmice između kola i minuti

Izvor je Flashscore (javni feed koji koristi njihov sajt):
  dnevni spisak utakmica   f_3_<pomak>_1_en_1          (za ključeve timova u Evroligi)
  stranica tima            /team/<slug>/<id>/results/   (sve utakmice sezone i raspored)
  statistika igrača        df_psn_1_<id utakmice>       (minuti, poeni, skokovi, asistencije)
Izlaz u procene/podaci/domace/:
  timovi.json      šifra tima u Evroligi -> id, slug i ime na Flashscore-u
  utakmice.json    <id>:<šifra tima> -> dict(id, t, liga, dom, gost, kod, rez, igraci{kod: [[ime, min, P, S, A], ...]}) za završene utakmice
  raspored.json    kod -> buduće utakmice van Evrolige [[t, liga, protivnik, kod kuće]]
Cilj: posle nekoliko kola videti da li domaća utakmica između kola (i minuti u njoj) utiče na minute i učinak u Evroligi.
"""
import argparse, collections, datetime as dt, json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, ucitaj, sacuvaj, tim, utakmice

FEED = 'https://global.flashscore.ninja/2/x/feed/'
SAJT = 'https://www.flashscore.com'
ZAG = {'x-fsign': 'SW9D1eZo', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}
FOLDER = os.path.join(PROCENE, 'podaci', 'domace')
POCETAK = dt.datetime(2026, 8, 15, tzinfo=dt.timezone.utc).timestamp()


def get(url):
    for pokusaj in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=ZAG), timeout=30) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            if pokusaj == 2:
                print('  ne mogu:', url, e)
                return ''
            time.sleep(2)


def dogadjaji(tekst):
    """Flashscore format: zapisi odvojeni sa ~, polja sa ¬, ključ÷vrednost. Vraća (liga, polja) za svaku utakmicu."""
    liga = None
    for b in tekst.split('~'):
        f = dict(x.split('÷', 1) for x in b.split('¬') if '÷' in x)
        if 'ZA' in f:
            liga = f['ZA']
        if 'AA' in f and 'AD' in f:
            yield liga, f


def je_evroliga(liga):
    return bool(liga) and 'euroleague' in liga.lower()


def preskoci(liga):
    """Evroliga (imamo je iz zvaničnih zapisnika), ženske lige i prijateljske utakmice."""
    l = (liga or '').lower()
    return 'euroleague' in l or 'women' in l or 'friendly' in l


def timovi(stari):
    """Ključevi timova iz dnevnih spiskova (Evroliga, ±7 dana)."""
    out = dict(stari)
    for pomak in range(-7, 8):
        if len(out) >= 20:
            break
        for liga, f in dogadjaji(get(f'{FEED}f_3_{pomak}_1_en_1')):
            if (liga or '').strip() != 'EUROPE: Euroleague':      # bez ženske Evrolige
                continue
            for ime, i, slug, skr in ((f.get('AE'), f.get('PX'), f.get('WU'), f.get('WM')), (f.get('AF'), f.get('PY'), f.get('WV'), f.get('WN'))):
                kod = tim(ime or '')
                if kod and kod not in out and i and slug and not (ime or '').endswith(' W'):
                    out[kod] = dict(id=i, slug=slug, ime=ime, skr=skr)
    return out


def igraci_utakmice(eid):
    """df_psn: zaglavlje kolona (PF) pa igrači (PJ ime, PN skraćenica tima, PC vrednosti odvojene sa |)."""
    t = get(f'{FEED}df_psn_1_{eid}')
    kol, out = [], collections.defaultdict(list)
    for b in t.split('~'):
        f = dict(x.split('÷', 1) for x in b.split('¬') if '÷' in x)
        if 'PA' in f and kol:          # samo prva tabela (ukupno)
            break
        if 'PF' in f and 'PJ' not in f:
            kol.append(f['PF'])
        if 'PJ' in f and 'PC' in f:
            v = dict(zip(kol[1:], f['PC'].split('|')))
            m = v.get('MIN', '-')
            mins = (int(m.split(':')[0]) + int(m.split(':')[1]) / 60) if ':' in m else float(m) if m.isdigit() else 0.0
            br = lambda x: int(v.get(x)) if (v.get(x) or '-').lstrip('-').isdigit() else 0
            out[f.get('PN', '?')].append([f['PJ'], round(mins, 1), br('PTS'), br('REB'), br('AST')])
    return dict(out)


def osvezi():
    os.makedirs(FOLDER, exist_ok=True)
    pt, pu, pr = (os.path.join(FOLDER, x) for x in ('timovi.json', 'utakmice.json', 'raspored.json'))
    T = timovi(ucitaj(pt) if os.path.exists(pt) else {})
    sacuvaj(pt, T)
    U = ucitaj(pu) if os.path.exists(pu) else {}
    rasp, novih = {}, 0
    sad = time.time()
    for kod, x in sorted(T.items()):
        strana = get(f"{SAJT}/team/{x['slug']}/{x['id']}/results/")
        if not strana:
            continue
        vidjeno, buduce = set(), []
        for liga, f in dogadjaji(strana[strana.find('SA÷'):]):
            eid = f['AA']
            if eid in vidjeno or preskoci(liga):
                continue
            vidjeno.add(eid)
            t0 = int(f['AD'])
            if t0 < POCETAK:
                continue
            kuca = f.get('PX') == x['id']
            prot = f.get('AF') if kuca else f.get('AE')
            if t0 > sad:
                buduce.append([t0, liga, prot, kuca])
                continue
            if f.get('AB') != '3':        # nije završena
                continue
            kljuc = f'{eid}:{kod}'          # utakmica dva tima iz Evrolige se čuva za svaki tim posebno
            if kljuc in U and U[kljuc].get('igraci'):
                continue
            ig = igraci_utakmice(eid)
            U[kljuc] = dict(id=eid, t=t0, liga=liga, dom=f.get('AE'), gost=f.get('AF'), kod=kod, kuca=kuca,
                          rez=[f.get('AG'), f.get('AH')], skr=[f.get('WM'), f.get('WN')], igraci=ig)
            novih += 1
            time.sleep(0.4)
        rasp[kod] = sorted(buduce)[:8]
        time.sleep(0.6)
    sacuvaj(pu, U)
    sacuvaj(pr, rasp)
    bez = sum(1 for u in U.values() if not u.get('igraci'))
    print(f'domaće: timova {len(T)}, utakmica {len(U)} (novih {novih}, bez statistike igrača {bez})')


def pregled():
    """Za svaki tim: broj domaćih utakmica i koliko ih je bilo između dva kola Evrolige, prosečni minuti rotacije."""
    U = ucitaj(os.path.join(FOLDER, 'utakmice.json'))
    T = ucitaj(os.path.join(FOLDER, 'timovi.json'))
    el = collections.defaultdict(list)
    for u in utakmice():
        if u.get('odigrana'):
            el[u['dom']].append(u['utc'].timestamp())
            el[u['gost']].append(u['utc'].timestamp())
    for kod in sorted(T):
        D = sorted([u for u in U.values() if u['kod'] == kod], key=lambda u: u['t'])
        E = sorted(el.get(kod, []))
        izmedju = sum(1 for a, b in zip(E, E[1:]) if any(a < u['t'] < b for u in D))
        skr = None
        mins = collections.defaultdict(list)
        for u in D:
            sk = u['skr'][0] if u['kuca'] else u['skr'][1]
            for ime, m, *_ in u['igraci'].get(sk, []):
                if m > 0:
                    mins[ime].append(m)
        top = sorted(((sum(v) / len(v), k) for k, v in mins.items() if len(v) >= 2), reverse=True)[:3]
        print(f"{kod}: domaćih {len(D)}, razmaka između kola sa domaćom utakmicom {izmedju}/{max(0, len(E) - 1)}; "
              + ', '.join(f'{k} {m:.1f}' for m, k in top))


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--pregled', action='store_true')
    a = ap.parse_args()
    pregled() if a.pregled else osvezi()
