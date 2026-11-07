"""Provera spoja minus-modela i modela procena na svim ponudama (ponoviti posle svakog kola).

  python3 spoj/provera.py            (iz korena repozitorijuma)

Za svaku granicu iz ponuda (Admiral 8.-23.10. iz baza/ds_all.json, pa baza/ponude/<kladionica>/) računa, samo iz
utakmica pre dana granice: verovatnoću tržišta (bez marže), model procena i minus-model. Ishodi iz baza/rows.json
i procene/podaci/dopuna.json. Izlaz: spoj/provera/izvestaj.md i spoj/provera/skup.json.

Čist test za minus-model su kola od 8 naviše (koeficijenti minus-modela podešeni su na kolima 4-7).
"""
import collections, json, math, os, statistics as st, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import signali
from signali import lgt, MSIG_PRAG, W_MINUS_ISPOD, W_PROCENE_ISPOD

KOREN = signali.KOREN
OUT = os.path.join(KOREN, 'spoj', 'provera')


def ucitaj_ponude():
    import importlib.util
    sp = importlib.util.spec_from_file_location('provera_procene', os.path.join(KOREN, 'procene', 'skripte', 'provera.py'))
    m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    return m.ponude()


def sg(z):
    return 1 / (1 + math.exp(-z))


def roi(S, strana):
    if not S:
        return 0, 0.0, 0.0, 0.0
    h = [x['preko'] == (1 if strana == 'preko' else 0) for x in S]
    kv = [x['o'] if strana == 'preko' else x['u'] for x in S]
    return len(S), sum(h) / len(S), sum(kv) / len(S), sum((k - 1) if a else -1 for a, k in zip(h, kv)) / len(S)


def skup():
    S = signali.Signali()
    B = S.B
    os.chdir(KOREN)
    rez = []
    for x in ucitaj_ponude():
        k, _ = B.nadji_u_utakmici(x['p'], x.get('t'), x['tk'])
        if not k:
            continue
        danas = [r for r in B.byk[k] if r['dan'] == x['dan']]
        if not danas:
            continue
        r = danas[0]
        pm = S.procene_preko(k, x['dan'], r['team'], r['opp'], x['s'], x['l'])
        if pm is None:
            continue
        tr = (1 / x['o']) / (1 / x['u'] + 1 / x['o'])
        m = S.minus(k, x['dan'], r['team'], r['opp'], x['s'], x['l'], 1 - tr)
        if not m:
            continue
        rez.append(dict(izvor=x['izvor'], dan=x['dan'], kolo=r['r'], k=k, team=r['team'], s=x['s'], l=x['l'], u=x['u'], o=x['o'],
                        pm=round(pm, 4), tr=round(tr, 4), preko=1 if r[x['s']] > x['l'] else 0, **m))
    for x in rez:
        x['Lp'] = lgt(x['pm']) - lgt(x['tr'])     # procene ka PREKO, razlika od tržišta
        x['Lu'] = -x['msig']                      # minus-model okrenut ka PREKO
    return rez


def rang_dan(R, key):
    byd = collections.defaultdict(list)
    for x in R:
        byd[x['dan']].append(x)
    for L in byd.values():
        L.sort(key=lambda x: x[key])
        for i, x in enumerate(L):
            x[key + '_r'] = i / len(L)             # 0 = najjače ka ISPOD


def main():
    D = skup()
    os.makedirs(OUT, exist_ok=True)
    json.dump(D, open(os.path.join(OUT, 'skup.json'), 'w'))
    kola = sorted({x['kolo'] for x in D})
    test = [k for k in kola if k >= 8]
    L = []
    def red(ime, S, strana):
        n, h, kv, r = roi(S, strana)
        L.append(f'| {ime} | {n} | {h:.1%} | {kv:.2f} | {r:+.1%} |')
    zag = '| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |\n|---|---|---|---|---|'
    L.append('# Spoj minus-modela i modela procena: provera')
    L.append('')
    L.append(f'Granica sa ishodom: {len(D)} ({", ".join(sorted({x["izvor"] for x in D}))}), kola {kola[0]}-{kola[-1]}. '
             f'Čist test (posle podešavanja minus-modela): kola {test[0]}-{test[-1]}. Rang se računa unutar dana.')
    L.append('')
    for naslov, R in (('Admiral', [x for x in D if x['izvor'] == 'admiral' and x['kolo'] in test]),
                      ('Sve kladionice', [x for x in D if x['kolo'] in test])):
        for key in ('Lp', 'Lu'):
            rang_dan(R, key)
        L.append(f'## {naslov}, kola {test[0]}-{test[-1]}: ISPOD')
        L.append('')
        L.append(zag)
        red('uvek ispod', R, 'ispod')
        red('samo minus-model, najjačih 30% dana', [x for x in R if x['Lu_r'] < .3], 'ispod')
        red('samo procene, najjačih 30% dana', [x for x in R if x['Lp_r'] < .3], 'ispod')
        red('**oba se slažu (oba u najjačih 30%)**', [x for x in R if x['Lu_r'] < .3 and x['Lp_r'] < .3], 'ispod')
        red('minus da, procene ne', [x for x in R if x['Lu_r'] < .3 and x['Lp_r'] >= .3], 'ispod')
        red('procene da, minus ne', [x for x in R if x['Lp_r'] < .3 and x['Lu_r'] >= .3], 'ispod')
        L.append('')
        L.append(f'## {naslov}, kola {test[0]}-{test[-1]}: PREKO')
        L.append('')
        L.append(zag)
        red('uvek preko', R, 'preko')
        red('minus-model okrenut, najjačih 30% ka preko', [x for x in R if x['Lu_r'] >= .7], 'preko')
        red('procene, najjačih 30% ka preko', [x for x in R if x['Lp_r'] >= .7], 'preko')
        red('oba se slažu za preko', [x for x in R if x['Lu_r'] >= .7 and x['Lp_r'] >= .7], 'preko')
        L.append('')
    # minusi: verovatnoća za tikete
    A = [x for x in D if x['izvor'] == 'admiral' and x['u'] >= 1.60]
    for x in A:
        fu = 1 - x['tr']; mdev = lgt(x['mpu']) - lgt(fu) - 0.16; pdev = -x['Lp']
        x['p0'] = sg(lgt(fu) + W_MINUS_ISPOD * mdev); x['ev0'] = x['p0'] * x['u']
        x['p1'] = sg(lgt(fu) + W_MINUS_ISPOD * mdev + W_PROCENE_ISPOD * pdev); x['ev1'] = x['p1'] * x['u']
    for key in ('p0', 'ev0', 'p1', 'ev1'):
        for x in A:
            x['_' + key] = -x[key]
        rang_dan(A, '_' + key)
    for kk, nm in (([k for k in kola if 5 <= k < 8], 'kola 5-7'), (test, f'kola {test[0]}-{test[-1]}')):
        R = [x for x in A if x['kolo'] in kk]
        L.append(f'## Minusi (Admiral, kvota ispod ≥ 1,60), {nm}: najboljih 25% dana')
        L.append('')
        L.append(zag)
        red('sve', R, 'ispod')
        red('ranije: po verovatnoći (tržište + 0,15·minus)', [x for x in R if x['_p0_r'] < .25], 'ispod')
        red('ranije, po vrednosti (verovatnoća × kvota)', [x for x in R if x['_ev0_r'] < .25], 'ispod')
        red('novo: + 0,30·procene, po verovatnoći', [x for x in R if x['_p1_r'] < .25], 'ispod')
        red('**novo: + 0,30·procene, po vrednosti**', [x for x in R if x['_ev1_r'] < .25], 'ispod')
        L.append('')
    # procene: uslov slaganja za MINUS predloge
    G = collections.defaultdict(list)
    for x in D:
        G[(x['dan'], x['k'], x['s'], x['l'])].append(x)
    E = []
    for L2 in G.values():
        x = dict(L2[0]); x['tr'] = st.mean(z['tr'] for z in L2); x['u'] = max(z['u'] for z in L2); x['o'] = max(z['o'] for z in L2)
        x['msig'] = st.mean(z['msig'] for z in L2); E.append(x)
    def a_kola(k):
        R = [x for x in E if k - 2 <= x['kolo'] < k]
        if not R:
            return 0
        y = sum(x['preko'] for x in R) / len(R); a = 0
        for _ in range(40):
            m = sum(sg(a + 0.3 * lgt(x['pm']) + 0.7 * lgt(x['tr'])) for x in R) / len(R); a += (y - m) / max(1e-3, m * (1 - m))
        return a
    AK = {k: a_kola(k) for k in kola}
    for x in E:
        pc = sg(AK.get(x['kolo'], 0) + 0.3 * lgt(x['pm']) + 0.7 * lgt(x['tr']))
        x['edge_u'] = x['tr'] - pc; x['pc'] = pc
    for kk, nm in (([k for k in kola if 5 <= k < 8], 'kola 5-7'), (test, f'kola {test[0]}-{test[-1]}')):
        R = [x for x in E if x['kolo'] in kk]
        M = [x for x in R if x['edge_u'] >= 0.06 and 1 - x['pc'] >= 0.54 and x['u'] >= 1.5]
        L.append(f'## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), {nm}')
        L.append('')
        L.append(zag)
        red('svi kandidati', M, 'ispod')
        red(f'**minus-model se slaže (msig ≥ {MSIG_PRAG})**', [x for x in M if x['msig'] >= MSIG_PRAG], 'ispod')
        red('izbačeni (minus-model se ne slaže)', [x for x in M if x['msig'] < MSIG_PRAG], 'ispod')
        L.append('')
    open(os.path.join(OUT, 'izvestaj.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
