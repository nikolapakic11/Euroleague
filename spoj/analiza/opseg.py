"""Opseg poena igrača (Admiral specijal, 19.11.2026): koliko vrede ponuđeni opsezi po istoriji i našoj proceni.
  python3 spoj/analiza/opseg.py baza/ponude/admiral/2026-11-19_opseg_poena.txt minusi/arhiva/kola/r13d1/sel_b.json
Za svaki par iz istorije (Admiral, poeni) gleda razliku stvarno − granica; za današnjeg igrača uzima parove sa sličnom
granicom (±3) i sličnom procenom minusa (±0,06) i iz njih računa koliko često bi pao u ponuđeni opseg."""
import io, os, sys, json, contextlib, unicodedata, bisect
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(R, 'spoj/analiza/an3.py'), encoding='utf8').read()
src = src[:src.index("print('  po stavci (p3")]
g = {'__file__': os.path.join(R, 'spoj/analiza/an3.py'), '__name__': 'an3_deo'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, 'an3', 'exec'), g)
F = [x for x in g['F'] if x['s'] == 'P' and x.get('act') is not None and x.get('actmin', 1) > 0]
for x in F: x['mix'] = (x['p3'] + 1 - x['pm']) / 2
print(f'istorija: {len(F)} parova (poeni, igrao)')

def nk(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower().replace('-', ' ').replace('.', '')
    return ' '.join(w for w in s.split() if w not in ('jr', 'iii', 'iv'))
ponuda, sel = sys.argv[1], sys.argv[2]
S = {nk(x['p']): x for x in json.load(open(sel)) if x['s'] == 'P'}
def verovatnoca(l, p, a, b):
    """P(a <= X <= b) iz sličnih parova; vraća (sa b uključeno, bez b) i broj parova"""
    sl = [x for x in F if abs(x['l'] - l) <= 3 and abs(x['mix'] - p) <= 0.06]
    if len(sl) < 60:
        sl = [x for x in F if abs(x['l'] - l) <= 4 and abs(x['mix'] - p) <= 0.10]
    d = [x['act'] - x['l'] for x in sl]
    n = len(d)
    inc = sum(a - l <= z <= b - l for z in d) / n
    exc = sum(a - l <= z <= b - 1 - l for z in d) / n
    return inc, exc, n
out = []
for red in open(ponuda, encoding='utf8').read().strip().split(';'):
    ime, vreme, op = red.split('|')
    x = S.get(nk(ime))
    if not x or not op: continue
    p = (x['pr'] + 1 - x['pm']) / 2 if x['pm'] is not None else x['pr']
    for o in op.split(','):
        r, k = o.split(':'); a, b = map(int, r.split('-')); k = float(k)
        inc, exc, n = verovatnoca(x['l'], p, a, b)
        out.append(dict(ime=ime, l=x['l'], p=p, r=r, k=k, inc=inc, exc=exc, n=n, ev_inc=inc * k - 1, ev_exc=exc * k - 1, g=x['g']))
print(f"\n{'igrač':20} {'gran':>5} {'minus':>6} {'opseg':>6} {'kvota':>5} | {'P (sa gornjom)':>14} {'EV':>6} | {'P (bez gornje)':>14} {'EV':>6} | n")
for o in sorted(out, key=lambda o: -o['ev_exc']):
    print(f"{o['ime'][:20]:20} {o['l']:5} {o['p']:6.2f} {o['r']:>6} {o['k']:5.2f} | {o['inc']:14.1%} {o['ev_inc']:+6.0%} | {o['exc']:14.1%} {o['ev_exc']:+6.0%} | {o['n']}")
print('\nproseci: EV sa gornjom granicom', f"{sum(o['ev_inc'] for o in out)/len(out):+.1%}", '| bez gornje', f"{sum(o['ev_exc'] for o in out)/len(out):+.1%}")
json.dump(out, open('/tmp/opseg_out.json', 'w'), ensure_ascii=False)
