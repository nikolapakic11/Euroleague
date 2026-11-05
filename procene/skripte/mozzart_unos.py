"""Pretvara izlaz Mozzart čitača (procene/alati/mozzart_citac.js) u snimak ponude baza/ponude/mozzart/<dan>_<slovo>.json.

  python3 procene/skripte/mozzart_unos.py ulaz.txt [--dan 2026-11-05]

Ulaz: red po utakmici, "<ID>@<Domaćin> - <Gost>#igrač|stavka|granica|ispod|preko;..." (npr. "1175959@Efes - Paris#A.Dokossi|P|5.5|1.95|1.85;...").
Imena timova su kao na Mozzartu; model po njima nalazi utakmicu i igrače. m=1 je glavna granica (kvote najbliže).
"""
import argparse, datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, sledece_slovo

ap = argparse.ArgumentParser(); ap.add_argument('ulaz'); ap.add_argument('--dan')
a = ap.parse_args()
dan = a.dan or dt.date.today().isoformat()
picks = []
for red in open(a.ulaz, encoding='utf-8'):
    if '#' not in red:
        continue
    glava, ostatak = red.strip().split('#', 1)
    c, _, par = glava.partition('@')
    tt = ' | '.join(x.strip() for x in par.split(' - ')) if par else ''
    G = {}
    for e in ostatak.split(';'):
        p, s, l, u, o = e.split('|')
        if o in ('', 'null'):
            continue
        G.setdefault((p, s), []).append(dict(c=c, p=p, t=tt, s=s, l=float(l), u=float(u), o=float(o), time=dan, liga='Evroliga'))
    for L in G.values():
        b = min(L, key=lambda z: abs(z['u'] - z['o']))
        for z in L:
            z['m'] = 1 if z is b else 0
            picks.append(z)
folder = os.path.join(BAZA, 'ponude', 'mozzart')
slovo = sledece_slovo(folder, dan)
put = os.path.join(folder, f'{dan}_{slovo}.json')
json.dump(dict(v=2, src='mozzart', at=dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), pomocnik='tekst stranice utakmice',
               el=None, picks=picks), open(put, 'w'), ensure_ascii=False)
print(put, len(picks), 'granica')
