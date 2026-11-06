"""Provera prilagođavanja (povratak i odsustvo saigrača) na svim ponudama od oktobra, 6.11.2026.

  python3 procene/provera/prilagodjavanje_2026-11-06.py      (posle provera.py)

Za svaku granicu iz procene/provera/granice.json pravi se ceo tim za tu utakmicu kao u tabli (model za svakog igrača,
ko nije igrao = odsutan, iz zapisnika), pa se primenjuje svaka varijanta prilagođavanja. Poredi se:
  - tačnost očekivanja i log gubitak modela na granicama igrača kojima je varijanta promenila očekivanje
  - walk-forward predlozi (spajanje podešeno samo na ranijim kolima, na istoj varijanti), kola 5–10
Napomena: odsutni su ovde svi koji nisu igrali (posle utakmice se zna), uživo samo potvrđeni.
"""
import collections, copy, json, math, os, statistics as st, sys
KOREN = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(KOREN, 'procene', 'skripte'))
os.chdir(KOREN)
import model, spajanje as S, prilagodjavanje as PJ
from model import Baza, verovatnoca_preko

model.ucitaj_parametre()
P = model.PAR
B = Baza()
R = json.load(open('procene/provera/granice.json'))
info = {(x['k'], x['dan']): x for x in B.rows}
po_g_tim = collections.defaultdict(set)
tim_g = collections.defaultdict(list)
for r in sorted(B.rows, key=lambda r: r['d']):
    po_g_tim[(r['g'], r['team'])].add(r['k'])
    if r['g'] not in tim_g[r['team']]:
        tim_g[r['team']].append(r['g'])
dan_g = {r['g']: r['dan'] for r in B.rows}

VAR = {'sirovo': None, 'staro': PJ.STARO, 'novo': PJ.NOVO,
       'novo bez glavne opcije': dict(PJ.NOVO, ods_glavni=0.0),
       'novo bez ograničenja': dict(PJ.NOVO, max_promena=None)}

grupe = collections.defaultdict(list)
for r in R:
    x = info.get((r['k'], r['dan']))
    if x:
        r['g'], r['team'], r['opp'] = x['g'], x['team'], x['opp']
        grupe[(x['g'], x['team'])].append(r)

mu_var = {v: {} for v in VAR}           # (g, k, s) -> (mu, var, promenjeno)
for (g, kod), linije in grupe.items():
    dan = linije[0]['dan']; opp = linije[0]['opp']
    pre_g = [gg for gg in tim_g[kod] if dan_g[gg] < dan]
    kljucevi = {r['k'] for r in B.rows if r['team'] == kod and r['dan'] < dan}
    igraci = []
    for k in kljucevi:
        e = B.procena(k, dan, kod, opp)
        if not e:
            continue
        odig = {r['g'] for r in B.byk[k]}
        igraci.append(dict(k=k, ime=k, pos=e['pos'], n=e['n'], min=e['min'], ne_igra=k not in po_g_tim[(g, kod)],
                           odsutan=sum(1 for gg in pre_g[-3:] if gg not in odig), rucno_min=None,
                           s={s: dict(mu=e['s'][s]['mu'], var=e['s'][s]['var'], A=P['A'][s],
                                      C=P['C'][s] * (1 + P['CV'] * e['min_cv'])) for s in 'PSA'}))
    # uloga u timu: odsutni rotacioni igrač (kao u tabli), glavne opcije (prva dva po očekivanim poenima) i
    # direktna zamena (ista pozicija kao odsutni, najviše minuta)
    n_tim = len(pre_g)
    van = [j for j in igraci if j['ne_igra'] and j['min'] >= 15 and n_tim and j['n'] >= 0.5 * n_tim and j['odsutan'] < 3]
    akt = sorted([i for i in igraci if not i['ne_igra']], key=lambda i: -i['s']['P']['mu'])
    zamene = set()
    for j in van:
        ista = sorted([i for i in akt if i['pos'] == j['pos']], key=lambda i: -i['min'])
        if ista:
            zamene.add(ista[0]['k'])
    for r in linije:
        r['tim_van'] = bool(van)
        r['glavni'] = r['k'] in {i['k'] for i in akt[:2]} or r['k'] in zamene
    for v, par in VAR.items():
        I = copy.deepcopy(igraci)
        PJ.prilagodi(I, B, kod, dan, len(pre_g), par)
        for i in I:
            for s in 'PSA':
                x = i['s'][s]
                mu_var[v][(g, i['k'], s)] = (x['mu'], x['var'], abs(x['mu'] - x['mu0']) > 0.01)


def pm_za(v, r):
    t = mu_var[v].get((r['g'], r['k'], r['s']))
    if not t:
        return r['pm'], False
    mu, var, prom = t
    if v == 'sirovo':
        return r['pm'], False
    return verovatnoca_preko(r['s'], mu, max(var, mu * 1.0001), r['l']), prom


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


for r in R:
    if 'g' not in r:
        continue
    for v in VAR:
        r[f'pm_{v}'], r[f'pr_{v}'] = pm_za(v, r)
        t = mu_var[v].get((r['g'], r['k'], r['s']))
        r[f'mu_{v}'] = t[0] if t else r['mu']
R = [r for r in R if 'g' in r]

out = dict(tacnost={}, izbor={})
# 1) tačnost na granicama koje bar jedna varijanta menja
for v in VAR:
    if v == 'sirovo':
        continue
    X = [r for r in R if r[f'pr_{v}']]
    if not X:
        continue
    d = dict(n=len(X),
             ll_sirovo=round(st.mean(ll(r['pm'], r['preko']) for r in X), 4),
             ll_var=round(st.mean(ll(r[f'pm_{v}'], r['preko']) for r in X), 4),
             ll_kvote=round(st.mean(ll(r['tr'], r['preko']) for r in X), 4),
             greska_sirovo=round(st.mean(r['ishod'] - r['mu'] for r in X), 2),
             greska_var=round(st.mean(r['ishod'] - r[f'mu_{v}'] for r in X), 2),
             mae_sirovo=round(st.mean(abs(r['ishod'] - r['mu']) for r in X), 2),
             mae_var=round(st.mean(abs(r['ishod'] - r[f'mu_{v}']) for r in X), 2))
    out['tacnost'][v] = d
    print(f"{v:24} granica {d['n']:4} | log gubitak sirovo {d['ll_sirovo']} → {d['ll_var']} (kvote {d['ll_kvote']}) | "
          f"prosečna greška {d['greska_sirovo']:+.2f} → {d['greska_var']:+.2f} | MAE {d['mae_sirovo']} → {d['mae_var']}")

# 2) walk-forward predlozi; dve kombinacije sa sirovim: 'novo, samo naniže' (prilagođavanje može samo da smanji
#    verovatnoću izabrane strane, nikad da je poveća) i 'novo, prosek sa sirovim'
kola = sorted({r['kolo'] for r in R})
KOMB = {'novo, samo naniže': min, 'novo, prosek sa sirovim': lambda a, b: (a + b) / 2,
        'naniže + tim sa odsutnim bez MINUS': min, 'naniže + bez MINUS + PLUS samo glavni': min,
        'naniže + bez MINUS, bez dopune do 6 kad tim nema MINUS': min}
for v in list(VAR) + list(KOMB):
    P_all = []
    for k in kola:
        vv = 'novo' if v in KOMB else v
        ranije = [dict(r, pm=r[f'pm_{vv}']) for r in R if r['kolo'] < k]
        if len(ranije) < 250:
            continue
        w = S.podesi(ranije)
        w0 = S.podesi([dict(r) for r in R if r['kolo'] < k]) if v in KOMB else None
        C = collections.defaultdict(list)
        bez_min_g = set()
        for r in R:
            if r['kolo'] != k:
                continue
            p = S.preko(w, r['s'], r[f'pm_{vv}'], r['tr'])
            p0 = S.preko(w0, r['s'], r['pm'], r['tr']) if w0 else None
            for strana, pp, kv, ok in (('o', p, r['o'], r['preko'] == 1), ('u', 1 - p, r['u'], r['preko'] == 0)):
                if w0:
                    pp = KOMB[v](pp, p0 if strana == 'o' else 1 - p0)
                if 'bez MINUS' in v and r['tim_van'] and strana == 'u':
                    continue
                if 'samo glavni' in v and r['tim_van'] and strana == 'o' and not r['glavni']:
                    continue
                if r['tim_van']:
                    bez_min_g.add(r['g'])
                C[r['g']].append(dict(igr=r['k'], tim=r['team'], s=r['s'], strana=strana, pp=pp, ev=pp * kv - 1, k=kv,
                                      prosao=ok, kolo=k, prom=r[f'pr_{vv}']))
        for g, CC in C.items():
            if 'bez dopune' in v and g in bez_min_g:
                stari = S.MIN_UT; S.MIN_UT = 0
                P_all += S.izbor_utakmice(CC)
                S.MIN_UT = stari
            else:
                P_all += S.izbor_utakmice(CC)

    def z(X):
        if not X:
            return dict(n=0)
        n = len(X); pr = sum(x['prosao'] for x in X); d = sum((x['k'] - 1) if x['prosao'] else -1 for x in X)
        return dict(n=n, prosao=pr, pogodak=round(pr / n, 3), povracaj=round(d / n, 3))
    o = dict(sve=z(P_all), plus=z([x for x in P_all if x['strana'] == 'o']), minus=z([x for x in P_all if x['strana'] == 'u']),
             prilagodjeni=z([x for x in P_all if x['prom']]), prilagodjeni_plus=z([x for x in P_all if x['prom'] and x['strana'] == 'o']))
    out['izbor'][v] = o
    f = lambda d: f"{d.get('prosao', 0)}/{d['n']} {d.get('pogodak', 0):.1%} {d.get('povracaj', 0):+.1%}" if d['n'] else '—'
    print(f"{v:24} predlozi {f(o['sve'])} | PLUS {f(o['plus'])} | MINUS {f(o['minus'])} | prilagođeni {f(o['prilagodjeni'])} (PLUS {f(o['prilagodjeni_plus'])})")
json.dump(out, open('procene/provera/prilagodjavanje_2026-11-06.json', 'w'), ensure_ascii=False, indent=1)
