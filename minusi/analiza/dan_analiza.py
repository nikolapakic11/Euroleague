"""Analiza jednog dana posle utakmica: prolaz minusa u celoj ponudi, izboru, odigranim parovima, po redovima, utakmicama i stavkama."""
import json, sys, re, unicodedata, collections, os, statistics as st
D = 'minusi/arhiva/kola/r12d1'
def nk(x):
    x = unicodedata.normalize('NFD', str(x)); x = ''.join(c for c in x if unicodedata.category(c) != 'Mn').lower()
    x = re.sub(r"[.']", '', x); x = re.sub(r'-', ' ', x); x = re.sub(r'[^a-z ,]', '', x)
    if ',' in x: s, f = x.split(',', 1); x = f.strip() + ' ' + s.strip()
    return ' '.join(w for w in x.split() if w not in {'jr', 'sr', 'ii', 'iii', 'iv'})
def minute(m):
    if not m or m == 'DNP': return 0.0
    p = str(m).split(':'); return int(p[0]) + int(p[1]) / 60
BOX = {}; GM = {}
for g in range(111, 120):
    d = json.load(open(f'baza/zapisnici/{g}.json'))
    for s in d['Stats']:
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
def ishod(p, s, l):
    b = nadji(p)
    if not b or b['min'] == 0: return None
    return b[s] < l
def prolaz(L, nm):
    r = [ishod(x['p'], x['s'], x['l']) for x in L]; r = [v for v in r if v is not None]
    print(f"  {nm}: {sum(r)}/{len(r)} = {sum(r)/len(r)*100:.0f}%" if r else f"  {nm}: -")
    return sum(r), len(r)
print('== Cela ponuda Admiral (minus) ==')
for f in ('a', 'c'):
    P = json.load(open(f'baza/ponude/admiral/2026-11-17_{f}.json'))['picks']; prolaz(P, f'ponuda {f}')
    for s in 'PSA': prolaz([x for x in P if x['s'] == s], f'   {s}')
print('== Izbor (bazen) ==')
S1 = json.load(open(f'{D}/sel_t1.json')); prolaz(S1, 'bazen talas 1 (46 igrača)')
S2 = json.load(open(f'{D}/sel_t2c.json'))
for r in (1, 2, 3): prolaz([x for x in S2 if x.get('red') == r], f'bazen talas 2, red {r} ({ {1:"oba modela",2:"jedan model",3:"van modela"}[r]})')
SA = json.load(open(f'{D}/sel_c75.json'))
SA.sort(key=lambda x: -x['pr'])
for a, b in ((0, 20), (20, 40), (40, 60), (60, 100), (100, 160)):
    prolaz(SA[a:b], f'spoj rang {a+1}-{b} (ponuda 15:27)')
print('== Odigrani parovi ==')
for f, nm in (('minusi/planovi/plan_admiral_110_17nov_talas1.txt', 'talas 1'), ('minusi/planovi/plan_admiral_60_17nov_talas2b.txt', 'talas 2')):
    T = json.load(open(f))['tickets']
    legs = {(l['p'], l['s'], l['l']): l for t in T for l in t['legs']}
    cnt = collections.Counter((l['p'], l['s'], l['l']) for t in T for l in t['legs'])
    L = [dict(p=k[0], s=k[1], l=k[2]) for k in legs]
    h, n = prolaz(L, f'{nm}: različiti parovi')
    rr = [(ishod(*k), c) for k, c in cnt.items()]; rr = [(v, c) for v, c in rr if v is not None]
    print(f"     po pojavljivanju: {sum(c for v,c in rr if v)}/{sum(c for v,c in rr)} = {sum(c for v,c in rr if v)/sum(c for v,c in rr)*100:.0f}%")
    for s in 'PSA': prolaz([x for x in L if x['s'] == s], f'     {s}')
print('== Po utakmicama (svi odigrani parovi) ==')
T = json.load(open('minusi/planovi/plan_admiral_110_17nov_talas1.txt'))['tickets'] + json.load(open('minusi/planovi/plan_admiral_60_17nov_talas2b.txt'))['tickets']
legs = {(l['p'], l['s'], l['l']) for t in T for l in t['legs']}
byg = collections.defaultdict(list)
for k in legs:
    b = nadji(k[0])
    if b and b['min'] > 0: byg[b['g']].append(b[k[1]] < k[2])
for g in sorted(byg):
    d = json.load(open(f'baza/zapisnici/{g}.json')); q = d['ByQuarter']
    sc = [sum((t.get(k) or 0) for k in ('Quarter1', 'Quarter2', 'Quarter3', 'Quarter4', 'Extra1')) for t in q]
    v = byg[g]; print(f"  {g} {q[0]['Team'][:14]}–{q[1]['Team'][:14]} {sc[0]}:{sc[1]} (zbir {sum(sc)}): {sum(v)}/{len(v)} = {sum(v)/len(v)*100:.0f}%")
print('== Spuštene granice ==')
prolaz([x for x in SA if x.get('spustena')], 'spuštene (ponuda 15:27)')
