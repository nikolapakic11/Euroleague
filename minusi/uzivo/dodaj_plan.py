"""Dodaje plan (fajl za Admiral pomoćnika) u aplikaciju, deo „Planovi od Claude-a“, sa procenama za simulaciju.

  python3 -I minusi/uzivo/dodaj_plan.py <plan.txt> <sel.json> --oznaka "13.11. 62 tiketa" [--opis "..."] [--kolo 11]

sel.json je izlaz izbor.py (procena 'pr' i fer verovatnoća 'fair' po paru). Piše u minusi/aplikacija/evroliga-minusi.html
i stanje.json; čuva poslednjih 15 planova. Posle toga objaviti aplikaciju (publish_files)."""
import argparse, json, os, re, sys, time, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from putanje import APP_HTML, MINUSI
ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('sel'); ap.add_argument('--oznaka', required=True)
ap.add_argument('--opis', default=''); ap.add_argument('--kolo', default='')
a = ap.parse_args()
P = json.load(open(a.plan)); S = {(x['p'], x['s'], x['l']): x for x in json.load(open(a.sel))}
T = []
for t in P['tickets']:
    legs = []
    for l in t['legs']:
        x = S.get((l['p'], l['s'], l['l']), {})
        legs.append(dict(c=l['c'], p=l['p'], t=l.get('t', ''), s=l['s'], l=l['l'], u=l['u'], pr=x.get('pr'), fa=x.get('fair'), g=x.get('g', '')))
    T.append(dict(stake=t['stake'], legs=legs))
def p1(key, n=20000):
    random.seed(7); keys = sorted({(l['p'], l['s'], l['l']) for t in T for l in t['legs']}); win = 0
    pv = {k: next((l[key] for t in T for l in t['legs'] if (l['p'], l['s'], l['l']) == k and l[key] is not None), 0.5) for k in keys}
    for _ in range(n):
        h = {k: random.random() < pv[k] for k in keys}
        win += any(all(h[(l['p'], l['s'], l['l'])] for l in t['legs']) for t in T)
    return round(win / n, 3)
cp = dict(id='cp' + str(int(time.time())), label=a.oznaka, desc=a.opis or f"{len(T)} tiketa, ukupno {sum(t['stake'] for t in T)} din.",
          at=time.strftime('%Y-%m-%dT%H:%M:%S'), round=a.kolo or P.get('round', ''), stats=dict(app=p1('pr'), market=p1('fa')), tickets=T)
def upisi(st):
    L = [x for x in (st.get('claudePlans') or []) if x.get('label') != cp['label']]
    st['claudePlans'] = (L + [cp])[-15:]; st['savedAt'] = int(time.time() * 1000)
h = open(APP_HTML, encoding='utf8').read()
pat = re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)', re.S)
st = json.loads(pat.search(h).group(2)); upisi(st)
open(APP_HTML, 'w', encoding='utf8').write(pat.sub(lambda m: m.group(1) + json.dumps(st, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c') + m.group(3), h, count=1))
sp = os.path.join(MINUSI, 'aplikacija', 'stanje.json'); s2 = json.load(open(sp)); upisi(s2); json.dump(s2, open(sp, 'w'), ensure_ascii=False, separators=(',', ':'))
print('dodat plan', cp['label'], '| bar jedan dobitni:', cp['stats'])
