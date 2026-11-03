"""Preuzimanje Soccerbet ponude za igrače Evrolige.

Upotreba:
  python3 procene/skripte/soccerbet.py            # Evroliga, novi snimak u baza/ponude/soccerbet/
  python3 procene/skripte/soccerbet.py --liga 2521028 --probno   # npr. Evrokup, samo ispis

Igrači su kategorija „PL“ u ligi (Evroliga 2516963 -> „Evroliga Igrači“).
Svaki igrač je jedan „meč“ (home = igrač, away = tim); pune kvote po igraču su na /match/{id}.
Snimak je u formatu v2 kao kod Admirala i MaxBeta, uz dodatke:
  - više granica po stavci (Soccerbet nudi alternativne), polje m=1 je glavna granica
    (kvote za ispod i preko najbliže jedna drugoj)
  - s: P poeni, S skokovi, A asistencije, 3 trojke, PR, PA, RA, PRA, ST ukradene, BL blokade, TO izgubljene
  - x: lestvice „N+“ (npr. 15+ poena) kao [igrač, tim, s, N, kvota]
  - dd: dabl-dabl [igrač, tim, da, ne]
"""
import argparse, datetime as dt, gzip, json, os, sys, time, urllib.request

sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, BG, sacuvaj, sledece_slovo, tim, nadji_utakmicu, utakmice

API = 'https://www.soccerbet.rs/restapi/offer/sr'
Q = 'annex=0&locale=sr'
EVROLIGA = 2516963

# tipTypeCode -> (stavka, strana)
LINIJE = {
    51681: ('P', 'u'), 51679: ('P', 'o'),
    51687: ('S', 'u'), 51685: ('S', 'o'),
    51684: ('A', 'u'), 51682: ('A', 'o'),
    51690: ('3', 'u'), 51688: ('3', 'o'),
    55246: ('PR', 'u'), 55244: ('PR', 'o'),
    55249: ('PA', 'u'), 55247: ('PA', 'o'),
    55252: ('RA', 'u'), 55250: ('RA', 'o'),
    55217: ('PRA', 'u'), 55215: ('PRA', 'o'),
    55674: ('ST', 'u'), 55672: ('ST', 'o'),
    55683: ('BL', 'u'), 55681: ('BL', 'o'),
    56171: ('TO', 'u'), 56169: ('TO', 'o'),
}
LESTVICE = {}
for n, c in zip([5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 60],
                [54096, 54101, 54106, 54111, 54116, 54121, 54126, 54131, 54136, 54141, 57454]):
    LESTVICE[c] = ('P', n)
for n, c in zip([3, 5, 7, 10, 13, 15, 17, 20], [54072, 54074, 54076, 54079, 54082, 54084, 54086, 54089]):
    LESTVICE[c] = ('S', n)
for n, c in zip([3, 5, 7, 10, 13, 15, 17, 20], [54050, 54052, 54054, 54057, 54060, 54062, 54064, 54067]):
    LESTVICE[c] = ('A', n)
for n, c in zip([1, 2, 3, 4, 5, 7, 8, 10], [54142, 54143, 54144, 54145, 54146, 54148, 54149, 54151]):
    LESTVICE[c] = ('3', n)
DD = {55831: 'da', 55832: 'ne'}


def get(path, pokusaja=3):
    url = f'{API}/{path}{"&" if "?" in path else "?"}{Q}'
    for i in range(pokusaja):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept-Encoding': 'gzip'})
            b = urllib.request.urlopen(req, timeout=30).read()
            if b[:2] == b'\x1f\x8b':
                b = gzip.decompress(b)
            return json.loads(b)
        except Exception as e:
            if i == pokusaja - 1:
                raise
            time.sleep(2 + 2 * i)


def lokalno(ms):
    return dt.datetime.fromtimestamp(ms / 1000, dt.timezone.utc).astimezone(BG)


def preuzmi(liga=EVROLIGA):
    lista = get(f'ext/sport/B/league/{liga}/PL/mob').get('esMatches') or []
    raspored = utakmice() if liga == EVROLIGA else None
    picks, x, dd, igraci = [], [], [], []
    for m in lista:
        if m.get('leagueCategory') != 'PL':
            continue
        try:
            pun = get(f'match/{m["id"]}')
        except Exception as e:
            print('greška za', m['home'], e, file=sys.stderr)
            pun = m
        bm = pun.get('betMap') or {}
        igrac, tm = m['home'], m['away']
        kod = tim(tm)
        t_loc = lokalno(m['kickOffTime'])
        g = None
        if raspored and kod:
            u = nadji_utakmicu(kod, t_loc.astimezone(dt.timezone.utc), raspored)
            g = u['g'] if u else None
        baza = dict(c=str(m['matchCode']), p=igrac, t=tm, time=t_loc.strftime('%Y-%m-%d %H:%M'), id=m['id'])
        if kod:
            baza['tk'] = kod
        if g:
            baza['g'] = g
        # linije: (s, granica) -> {u, o}
        lin = {}
        for tt, granice in bm.items():
            tt = int(tt)
            for sv, o in granice.items():
                kv = o.get('ov') or 0
                if kv <= 1 or o.get('s') == 'L':   # 0 = zaključano
                    continue
                if tt in LINIJE and sv.startswith('total='):
                    s, strana = LINIJE[tt]
                    lin.setdefault((s, float(sv.split('=')[1])), {})[strana] = kv
                elif tt in LESTVICE:
                    s, n = LESTVICE[tt]
                    x.append([igrac, tm, s, n, kv])
                elif tt in DD:
                    dd.append([igrac, tm, DD[tt], kv])
        po_stavci = {}
        for (s, l), k in lin.items():
            if 'u' in k and 'o' in k:
                po_stavci.setdefault(s, []).append((l, k['u'], k['o']))
        for s, lst in po_stavci.items():
            glavna = min(lst, key=lambda r: (abs(r[1] - r[2]), r[0]))[0]
            for l, u, o in sorted(lst):
                picks.append(dict(baza, s=s, l=l, u=u, o=o, m=1 if l == glavna else 0))
        igraci.append(igrac)
        time.sleep(0.15)
    # dd u parove
    ddp = {}
    for p, t, k, kv in dd:
        ddp.setdefault((p, t), {})[k] = kv
    return dict(v=2, src='soccerbet', at=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'),
                liga=liga, picks=picks, x=x,
                dd=[[p, t, v.get('da'), v.get('ne')] for (p, t), v in ddp.items()], el=None), len(igraci)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--liga', type=int, default=EVROLIGA)
    ap.add_argument('--probno', action='store_true', help='samo ispis, bez čuvanja')
    a = ap.parse_args()
    snimak, n = preuzmi(a.liga)
    glavne = [p for p in snimak['picks'] if p['m']]
    print(f'igrača {n}, granica {len(snimak["picks"])} (glavnih {len(glavne)}), lestvica {len(snimak["x"])}')
    from collections import Counter
    print('stavke (glavne):', dict(Counter(p['s'] for p in glavne)))
    bez = sorted({p['t'] for p in snimak['picks'] if 'tk' not in p})
    if bez:
        print('nepoznat tim:', bez)
    for p in glavne[:6]:
        print(' ', p['p'], p['t'], p['s'], p['l'], p['u'], p['o'], p['time'], p.get('g'))
    if a.probno or not snimak['picks']:
        if not snimak['picks']:
            print('ponuda je prazna, ništa nije sačuvano')
        return
    dan = dt.datetime.now(BG).date().isoformat()
    folder = os.path.join(BAZA, 'ponude', 'soccerbet')
    put = os.path.join(folder, f'{dan}_{sledece_slovo(folder, dan)}.json')
    sacuvaj(put, snimak, kompaktno=True)
    print('sačuvano', os.path.relpath(put, os.path.dirname(BAZA)))


if __name__ == '__main__':
    main()
