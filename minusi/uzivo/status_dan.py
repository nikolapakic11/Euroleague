"""Živi presek za odigrane tikete jednog dana.
  python3 minusi/uzivo/status_dan.py --planovi plan1.txt plan2.txt --utakmice 111 112 ... --dir /tmp/live12 [--sajt 2026-11-17]
Zapisnici se čitaju iz --dir/bs_N.json (fetch.sh). Stavka: prošla (završena utakmica, ispod), pala (već preko granice),
ide (još ispod), čeka (utakmica nije počela). Igrač koji ne igra (0 minuta u završenoj utakmici) = vraćeno (kvota 1).
"""
import json, argparse, re, unicodedata, collections, os, math
ap = argparse.ArgumentParser()
ap.add_argument('--planovi', nargs='+', required=True)
ap.add_argument('--utakmice', nargs='+', type=int, required=True)
ap.add_argument('--dir', default='/tmp/live12')
ap.add_argument('--sajt', default=None)
ap.add_argument('--detalj', action='store_true')
ap.add_argument('--gotove', nargs='*', type=int, default=[], help='utakmice koje su gotove, a API ih još vodi kao žive')
a = ap.parse_args()

def nk(x):
    x = unicodedata.normalize('NFD', str(x)); x = ''.join(c for c in x if unicodedata.category(c) != 'Mn').lower()
    x = re.sub(r"[.']", '', x); x = re.sub(r'-', ' ', x); x = re.sub(r'[^a-z ,]', '', x)
    if ',' in x: s, f = x.split(',', 1); x = f.strip() + ' ' + s.strip()
    return ' '.join(w for w in x.split() if w not in {'jr', 'sr', 'ii', 'iii', 'iv'})

def minute(m):
    if not m or m == 'DNP': return 0.0
    p = str(m).split(':'); return int(p[0]) + (int(p[1]) / 60 if len(p) > 1 else 0)

BOX = {}; GAME = {}; TIM = {}
for g in a.utakmice:
    f = os.path.join(a.dir, f'bs_{g}.json')
    if not os.path.exists(f): continue
    try: d = json.load(open(f))
    except Exception: continue
    q = d.get('ByQuarter') or []
    sc = [sum((t.get(k) or 0) for k in ('Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Extra1', 'Extra2', 'Extra3', 'Extratime1', 'Extratime2')) for t in q]
    nq = max([sum(1 for k in ('Quarter1', 'Quarter2', 'Quarter3', 'Quarter4') if t.get(k)) for t in q] or [0])
    mins = [sum(minute(p['Minutes']) for p in s['PlayersStats']) for s in d.get('Stats', [])]
    kraj = ((not d.get('Live')) and nq >= 4 and bool(sc) and sc[0] != sc[1]) or g in a.gotove
    GAME[g] = dict(score=sc, timovi=[t['Team'] for t in q], kraj=bool(kraj), min=round(min(mins or [0]) / 5, 1))
    for t in q: TIM[nk(t['Team'])] = g
    for s in d.get('Stats', []):
        for p in s['PlayersStats']:
            BOX[nk(p['Player'])] = dict(P=p['Points'], S=p['TotalRebounds'], A=p['Assistances'], min=minute(p['Minutes']), g=g)

def nadji(ime):
    k = nk(ime)
    if k in BOX: return BOX[k]
    w = k.split()
    for kk, v in BOX.items():
        ww = kk.split()
        if ww and w and ww[-1] == w[-1] and ww[0][:3] == w[0][:3]: return v
    return None

OPSTE = {'aviv', 'basketball', 'basket', 'club', 'sport'}   # 19.11.2026: „Hapoel Tel-Aviv“ se kačio na Makabi preko „aviv“
def igra_tima(tim):
    w = [x for x in nk(tim).replace(',', ' ').split() if len(x) >= 4 and x not in OPSTE]
    for tn, g in TIM.items():
        if any(x in tn.split() for x in w): return g
    return None

def stanje(l):
    b = nadji(l['p'])
    if not b:
        g = igra_tima(l.get('t', ''))
        if g is not None and GAME[g]['min'] > 0:   # tim igra, a igrača nema u zapisniku: nije u sastavu, par se vraća
            return 'vraćeno', 0, dict(P=0, S=0, A=0, min=0, g=g)
        return 'čeka', None, None
    v = b[l['s']]; gm = GAME[b['g']]
    if v >= l['l']: return 'pala', v, b
    if gm['kraj']: return ('vraćeno' if b['min'] == 0 else 'prošla'), v, b
    return 'ide', v, b

tik = []
for f in a.planovi:
    for t in json.load(open(f))['tickets']: tik.append((os.path.basename(f), t))
legs = {}
for _, t in tik:
    for l in t['legs']: legs[(l['p'], l['s'], l['l'])] = l
LS = {k: stanje(l) for k, l in legs.items()}
cnt = collections.Counter((k[0], k[1], k[2]) for _, t in tik for k in [(l['p'], l['s'], l['l']) for l in t['legs']])

for g, gm in GAME.items():
    print(f"utakmica {g}: {' – '.join(gm['timovi'])} {':'.join(map(str, gm['score']))} | {'KRAJ' if gm['kraj'] else 'oko ' + str(gm['min']) + ' min'}")
print()
for st in ('pala', 'ide', 'prošla', 'vraćeno'):
    L = [(k, v, b) for k, (s, v, b) in LS.items() if s == st]
    if not L: continue
    print(f"{st.upper()} ({len(L)}):")
    for k, v, b in sorted(L, key=lambda x: -cnt[x[0]]):
        print(f"   {k[0]} {k[1]} {k[2]}: sada {v} ({b['min']:.0f} min) – na {cnt[k]} tiketa")
nc = sum(1 for s in LS.values() if s[0] == 'čeka'); print(f"ČEKA: {nc} parova iz utakmica koje nisu počele\n")

for src in sorted({s for s, _ in tik}):
    T = [t for s, t in tik if s == src]
    raz = collections.Counter()
    for t in T:
        m = sum(1 for l in t['legs'] if LS[(l['p'], l['s'], l['l'])][0] == 'pala')
        raz[min(m, 3)] += 1
    print(f"{src}: {len(T)} tiketa | živih bez promašaja {raz[0]}, sa jednim promašajem {raz[1]}, sa dva {raz[2]}, sa tri i više {raz[3]}")
if a.sajt:
    try:
        d = json.load(open('/home/claude/Euroleague/procene/predlozi/kolo12.json'))
        print('\nSAJT:')
        for x in d['predlozi']:
            if x.get('dan') == a.sajt and not x.get('povucen'):
                b = nadji(x['ime'])
                if not b: print(f"   {x['ime']} {x['s']} {x['strana']} {x['l']}: čeka"); continue
                v = b[x['s']]; gm = GAME[b['g']]
                ok = (v < x['l']) if x['strana'] == 'u' else (v > x['l'])
                st = ('PROŠAO' if ok else 'PAO') if gm['kraj'] else ('pao' if (x['strana'] == 'u' and v >= x['l']) else 'prošao' if (x['strana'] == 'o' and v > x['l']) else 'ide')
                print(f"   {x['ime']} {x['s']} {'ispod' if x['strana']=='u' else 'preko'} {x['l']}: sada {v} ({b['min']:.0f} min) – {st}")
    except Exception as e:
        print('sajt: greška', e)
