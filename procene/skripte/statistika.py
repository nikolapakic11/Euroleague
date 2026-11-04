"""Statistika timova i igrača u ovoj sezoni, iz zapisnika (baza/zapisnici i procene/podaci/zapisnici iz dopune).

  python3 procene/skripte/statistika.py

Izlaz procene/podaci/statistika.json:
  liga     proseci lige po utakmici (za poređenje)
  timovi   kod -> ime, utakmice, pobede, poeni dati i primljeni, posedi (tempo), napad i odbrana na 100 poseda, skokovi
           (napad, odbrana, udeo uhvaćenih), asistencije date i dozvoljene, izgubljene lopte, trojke, slobodna bacanja,
           dozvoljeno po poziciji (bekovi, krila, centri) u poenima, skokovima i asistencijama, i mesto na tabeli za svaku meru
  igraci   ključ -> ime, tim, pozicija, utakmice, starter, minuti i učinak po utakmici, šut, udeo u poenima, skokovima i
           asistencijama tima (u utakmicama koje je igrao), PIR
Koriste je javna stranica (kartica Statistika) i obrazloženja predloga (predlozi.py).
"""
import collections, glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, PROCENE, ucitaj, sacuvaj, pn
from obrazlozenje import IME as OB_IME

POZ = {'Guard': 'G', 'Forward': 'F', 'Center': 'C'}


def minuti(m):
    if not m or ':' not in str(m):
        return 0.0
    a, b = str(m).split(':')
    return int(a) + int(b) / 60


def zapisnici():
    Z = {}
    for f in glob.glob(os.path.join(BAZA, 'zapisnici', '*.json')) + glob.glob(os.path.join(PROCENE, 'podaci', 'zapisnici', '*.json')):
        gc = int(os.path.basename(f)[:-5])
        d = ucitaj(f)
        if d and d.get('Stats') and len(d['Stats']) == 2 and all(s['PlayersStats'] for s in d['Stats']):
            Z[gc] = d
    return Z


def imena_timova():
    g = ucitaj(os.path.join(BAZA, 'games.json'))
    x = g['data'] if isinstance(g, dict) and 'data' in g else g
    out = {}
    for u in x:
        for s in ('local', 'road'):
            c = u[s]['club']
            out[c['code']] = c.get('editorialName') or c['name']
    return out


def pozicije():
    pos = {}
    for f in glob.glob(os.path.join(BAZA, 'rosteri', '*.json')):
        for x in ucitaj(f):
            if x.get('type') == 'J' and x.get('person'):
                pos[pn(x['person']['name'])] = POZ.get(x.get('positionName') or '', '')
    return pos


def lepo(n):
    if ',' in n:
        a, b = n.split(',', 1)
        return (b.strip().title() + ' ' + a.strip().title()).strip()
    return n.title()


def main():
    Z = zapisnici()
    IME = imena_timova()
    POS = pozicije()
    T = collections.defaultdict(lambda: collections.defaultdict(float))
    I = {}
    poz_dozv = collections.defaultdict(lambda: collections.defaultdict(lambda: [0, 0, 0]))   # (tim, g) -> poz -> P,S,A protivnika
    for gc, d in sorted(Z.items()):
        S = d['Stats']
        kod = [s['PlayersStats'][0]['Team'].strip() for s in S]
        tot = [s['totr'] for s in S]
        for j in (0, 1):
            a, b = tot[j], tot[1 - j]
            t = T[kod[j]]
            t['n'] += 1
            t['pob'] += a['Points'] > b['Points']
            for kl, polje in (('pts', 'Points'), ('fga2', 'FieldGoalsAttempted2'), ('fgm2', 'FieldGoalsMade2'), ('fga3', 'FieldGoalsAttempted3'),
                              ('fgm3', 'FieldGoalsMade3'), ('fta', 'FreeThrowsAttempted'), ('ftm', 'FreeThrowsMade'), ('or', 'OffensiveRebounds'),
                              ('dr', 'DefensiveRebounds'), ('ast', 'Assistances'), ('stl', 'Steals'), ('to', 'Turnovers'), ('blk', 'BlocksFavour')):
                t[kl] += a[polje]
                t['o_' + kl] += b[polje]
            pos_a = a['FieldGoalsAttempted2'] + a['FieldGoalsAttempted3'] + 0.44 * a['FreeThrowsAttempted'] - a['OffensiveRebounds'] + a['Turnovers']
            pos_b = b['FieldGoalsAttempted2'] + b['FieldGoalsAttempted3'] + 0.44 * b['FreeThrowsAttempted'] - b['OffensiveRebounds'] + b['Turnovers']
            t['pos'] += (pos_a + pos_b) / 2
            tp, ts, ta = a['Points'], a['OffensiveRebounds'] + a['DefensiveRebounds'], a['Assistances']
            for p in S[j]['PlayersStats']:
                m = minuti(p['Minutes'])
                if m <= 0:
                    continue
                k = pn(p['Player'])
                x = I.setdefault(k, dict(k=k, ime=lepo(p['Player']), tim=kod[j], pos=POS.get(k, ''), n=0, st=0, min=0.0, P=0, S=0, A=0, OR=0, DR=0,
                                         STL=0, TO=0, BLK=0, fgm2=0, fga2=0, fgm3=0, fga3=0, ftm=0, fta=0, PIR=0, pm=0, timP=0, timS=0, timA=0, posl=''))
                x['tim'] = kod[j]
                x['n'] += 1; x['st'] += p.get('IsStarter', 0); x['min'] += m
                x['P'] += p['Points']; x['S'] += p['TotalRebounds']; x['A'] += p['Assistances']
                x['OR'] += p['OffensiveRebounds']; x['DR'] += p['DefensiveRebounds']; x['STL'] += p['Steals']; x['TO'] += p['Turnovers']
                x['BLK'] += p['BlocksFavour']; x['fgm2'] += p['FieldGoalsMade2']; x['fga2'] += p['FieldGoalsAttempted2']
                x['fgm3'] += p['FieldGoalsMade3']; x['fga3'] += p['FieldGoalsAttempted3']; x['ftm'] += p['FreeThrowsMade']; x['fta'] += p['FreeThrowsAttempted']
                x['PIR'] += p['Valuation'] or 0; x['pm'] += p.get('Plusminus') or 0
                x['timP'] += tp; x['timS'] += ts; x['timA'] += ta
                ps = x['pos'] or POS.get(k, '')
                if ps in ('G', 'F', 'C'):
                    dz = poz_dozv[(kod[1 - j], gc)][ps]           # protivnik (kod[1-j]) dozvolio ovoj poziciji
                    dz[0] += p['Points']; dz[1] += p['TotalRebounds']; dz[2] += p['Assistances']
    # liga
    timovi = {}
    for kod, t in T.items():
        n = t['n']
        pg = lambda kl: t[kl] / n
        timovi[kod] = dict(
            ime=OB_IME.get(kod) or IME.get(kod, kod), n=int(n), pob=int(t['pob']), por=int(n - t['pob']),
            pts=round(pg('pts'), 1), o_pts=round(pg('o_pts'), 1), tempo=round(t['pos'] / n, 1),
            ortg=round(100 * t['pts'] / t['pos'], 1), drtg=round(100 * t['o_pts'] / t['pos'], 1),
            sk=round((t['or'] + t['dr']) / n, 1), o_sk=round((t['o_or'] + t['o_dr']) / n, 1),
            or_=round(pg('or'), 1), dr=round(pg('dr'), 1),
            or_pct=round(t['or'] / (t['or'] + t['o_dr']), 3), dr_pct=round(t['dr'] / (t['dr'] + t['o_or']), 3),
            ast=round(pg('ast'), 1), o_ast=round(pg('o_ast'), 1), to=round(pg('to'), 1), o_to=round(pg('o_to'), 1),
            stl=round(pg('stl'), 1), blk=round(pg('blk'), 1),
            fga3=round(pg('fga3'), 1), p3=round(t['fgm3'] / t['fga3'], 3) if t['fga3'] else 0, o_p3=round(t['o_fgm3'] / t['o_fga3'], 3) if t['o_fga3'] else 0,
            p2=round(t['fgm2'] / t['fga2'], 3) if t['fga2'] else 0, fta=round(pg('fta'), 1), pft=round(t['ftm'] / t['fta'], 3) if t['fta'] else 0)
    # dozvoljeno po poziciji, u odnosu na prosek lige
    sume = collections.defaultdict(lambda: [0, 0, 0, 0])
    for (kod, g), D in poz_dozv.items():
        for ps, v in D.items():
            s = sume[ps]; s[0] += v[0]; s[1] += v[1]; s[2] += v[2]; s[3] += 1
    lig_poz = {ps: [s[i] / s[3] for i in range(3)] for ps, s in sume.items()}
    for kod in timovi:
        dz = {}
        for ps in 'GFC':
            V = [D[ps] for (kd, g), D in poz_dozv.items() if kd == kod and ps in D]
            if V and ps in lig_poz:
                dz[ps] = {s: round(sum(v[i] for v in V) / len(V), 1) for i, s in enumerate('PSA')}
                dz[ps].update({'i' + s: round((sum(v[i] for v in V) / len(V)) / lig_poz[ps][i], 3) for i, s in enumerate('PSA')})
        timovi[kod]['poz'] = dz
    # mesta na tabeli (1 = najviše)
    for mera in ('pts', 'o_pts', 'tempo', 'ortg', 'drtg', 'sk', 'o_sk', 'or_pct', 'dr_pct', 'ast', 'o_ast', 'to', 'fga3', 'p3', 'o_p3'):
        red = sorted(timovi, key=lambda k: -timovi[k][mera])
        for i, k in enumerate(red, 1):
            timovi[k].setdefault('mesto', {})[mera] = i
    for ps in 'GFC':
        for s in 'PSA':
            K = [k for k in timovi if ps in timovi[k]['poz']]
            for i, k in enumerate(sorted(K, key=lambda k: -timovi[k]['poz'][ps]['i' + s]), 1):
                timovi[k]['poz'][ps]['m' + s] = i
    n_t = len(timovi)
    liga = dict(timova=n_t, utakmica=len(Z), pts=round(sum(t['pts'] for t in timovi.values()) / n_t, 1),
                tempo=round(sum(t['tempo'] for t in timovi.values()) / n_t, 1), sk=round(sum(t['sk'] for t in timovi.values()) / n_t, 1),
                ast=round(sum(t['ast'] for t in timovi.values()) / n_t, 1), poz={ps: [round(v, 1) for v in lig_poz[ps]] for ps in lig_poz})
    igraci = {}
    for k, x in I.items():
        n = x['n']
        igraci[k] = dict(k=k, ime=x['ime'], tim=x['tim'], pos=x['pos'], n=n, st=x['st'], min=round(x['min'] / n, 1),
                         P=round(x['P'] / n, 1), S=round(x['S'] / n, 1), A=round(x['A'] / n, 1), OR=round(x['OR'] / n, 1), DR=round(x['DR'] / n, 1),
                         STL=round(x['STL'] / n, 1), TO=round(x['TO'] / n, 1), BLK=round(x['BLK'] / n, 1), PIR=round(x['PIR'] / n, 1),
                         p2=[x['fgm2'], x['fga2']], p3=[x['fgm3'], x['fga3']], ft=[x['ftm'], x['fta']],
                         uP=round(x['P'] / x['timP'], 3) if x['timP'] else 0, uS=round(x['S'] / x['timS'], 3) if x['timS'] else 0,
                         uA=round(x['A'] / x['timA'], 3) if x['timA'] else 0)
    # mesto u timu po udelu (1 = najveći udeo), za igrače sa bar 3 utakmice
    for s in 'PSA':
        po_t = collections.defaultdict(list)
        for k, x in igraci.items():
            if x['n'] >= 3:
                po_t[x['tim']].append(k)
        for kod, K in po_t.items():
            for i, k in enumerate(sorted(K, key=lambda k: -igraci[k]['u' + s]), 1):
                igraci[k]['m' + s] = i
    sacuvaj(os.path.join(PROCENE, 'podaci', 'statistika.json'), dict(liga=liga, timovi=timovi, igraci=igraci), kompaktno=True)
    print(f'statistika: utakmica {len(Z)}, timova {n_t}, igrača {len(igraci)}')


if __name__ == '__main__':
    main()
