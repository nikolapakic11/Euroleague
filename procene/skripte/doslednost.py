"""Provera doslednosti onoga što stranica prikazuje (Nikola, 6.11.2026: „očekuješ 4,3, a naginje preko 5,5“).

  python3 procene/skripte/doslednost.py        (posle predlozi.py; čita procene/javno/predlozi.html)

Za svakog igrača i stavku proverava:
  1. prikazana strana (naginje) mora da se slaže sa očekivanjem modela naspram granice, osim kad piše „neodlučno“
  2. objavljeni predlog mora biti na strani očekivanja modela
  3. „neodlučno“ samo kad se model i kladionice zaista razilaze ili je verovatnoća ispod 53%
  4. prvi razlog („zašto“) ne sme da kaže da je granica viša od očekivanja kad je strana preko (i obrnuto)
  5. raspon (q) mora da sadrži očekivanje
Ispisuje svaku nedoslednost; 0 nedoslednosti = u redu.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE

h = open(os.path.join(PROCENE, 'javno', 'predlozi.html'), encoding='utf-8').read()
D = json.loads(re.search(r'id="podaci">(.*?)</script>', h, re.S).group(1))
greske, n = [], 0
for i in (D.get('igraci') or {}).get('igraci', []):
    for s in 'PSA':
        x = i['s'][s]; ng = x.get('ng')
        if not ng or x.get('mu') is None:
            continue
        n += 1
        mu, l = x['mu'], ng['l']
        model_o = mu > l
        id_ = f"{i['ime']} {s} {l}"
        if not ng.get('neodl') and (ng['strana'] == 'o') != model_o:
            greske.append(f'{id_}: naginje {ng["strana"]}, a očekivanje {mu}')
        if ng.get('neodl') and ng['pp'] >= 0.535:
            greske.append(f'{id_}: „bez jasne strane“, a verovatnoća {ng["pp"]}')
        pr = x.get('pred')
        if pr and (pr['strana'] == 'o') != (mu > pr['l']):
            greske.append(f'{id_}: predlog {pr["strana"]} {pr["l"]}, a očekivanje {mu}')
        z0 = (ng.get('zasto') or [''])[0]
        if not ng.get('neodl'):
            if ng['strana'] == 'o' and 'viša od onoga što realno očekujemo' in z0:
                greske.append(f'{id_}: strana preko, a razlog kaže da je granica viša od očekivanja')
            if ng['strana'] == 'u' and 'niža od onoga što realno očekujemo' in z0:
                greske.append(f'{id_}: strana ispod, a razlog kaže da je granica niža od očekivanja')
        q = x.get('q')
        if q and not (q[0] <= mu <= q[4]):
            greske.append(f'{id_}: očekivanje {mu} van raspona {q}')
for k in D['kola']:
    for p in k['predlozi']:
        if p.get('mu') is not None and p.get('ishod') is None and (p['strana'] == 'o') != (p['mu'] > p['l']):
            greske.append(f"predlog {p['ime']} {p['s']} {p['strana']} {p['l']}: očekivanje {p['mu']} na drugoj strani")
print(f'proverenih stavki: {n}, nedoslednosti: {len(greske)}')
for g in greske:
    print('  ' + g)
