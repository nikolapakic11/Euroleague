"""Prilagođavanje očekivanja kad se važan saigrač vrati ili kad potvrđeno ne igra (koristi ga tabla.py i provera).

Dva koraka posle modela (model.procena), na listi igrača jednog tima za utakmicu:
  povratak(igraci, B, kod, dan, PAR)   važan igrač (≥ 20 min) propustio ≥ 2 i vratio se u poslednjih 5
  odsustvo(igraci, n_tim, PAR)         rotacioni igrač potvrđeno ne igra: deo njegovih minuta ide saigračima

PAR je skup podešavanja; STARO je pravilo do 6.11.2026, NOVO je pravilo od 6.11.2026 (provera_2026-11-06.md):
  - na zapisnicima sezone efekat odsustva i povratka na saigrače je mali (nekoliko procenata), a staro pravilo je
    davalo +10 do +47%; odnos iz 2 utakmice je bio šum (Dokossi 1,47 iz 2 utakmice);
  - zato NOVO: povratak sa jačim skupljanjem (w = n/(n+4)) i odnosom u [0,85, 1,15]; od odsustva ide 40% minuta
    (umesto 85%), najviše +4 min po igraču; promena očekivanja najviše ±12%;
  - korist ide glavnom igraču koji direktno beneficira (Nikola, 6.11.): blago veći učinak po minutu samo za glavnu
    opciju tima (P, A), ostali dobijaju samo minute.
Igrač sa ručno zadatim minutima se ne menja. Raspon se računa ponovo iz očekivanja.
"""
from model import percentili

BLIZINA = {('G', 'G'): 1.0, ('F', 'F'): 1.0, ('C', 'C'): 1.0, ('G', 'F'): 0.6, ('F', 'G'): 0.6,
           ('F', 'C'): 0.6, ('C', 'F'): 0.6, ('G', 'C'): 0.2, ('C', 'G'): 0.2}

STARO = dict(pov_min=20.0, pov_k=1.5, pov_max_posle=5, pov_c={'P': 3.0, 'S': 1.5, 'A': 1.5}, pov_odnos=(0.5, 1.5),
             ods_udeo=0.85, ods_max_min=32.0, ods_dod_max=None, ods_glavni=0.0, max_promena=None)
NOVO = dict(STARO, pov_k=4.0, pov_odnos=(0.85, 1.15), ods_udeo=0.40, ods_dod_max=4.0, ods_glavni=0.04, max_promena=0.12)


def _postavi(x, mu):
    mu = max(0.05, mu)
    x['mu'] = round(mu, 2)
    x['var'] = round(x['A'] * mu + x['C'] * mu * mu, 2)
    x['q'] = percentili(x['mu'], x['var'])


def zapamti_sirovo(igraci):
    for i in igraci:
        i.setdefault('min0', i['min'])
        for s in 'PSA':
            i['s'][s].setdefault('mu0', i['s'][s]['mu'])
            i['s'][s].setdefault('var0', i['s'][s]['var'])


def ogranici(igraci, PAR):
    """Ukupna promena očekivanja posle oba koraka najviše ±max_promena od sirovog modela."""
    m = PAR.get('max_promena')
    if not m:
        return
    for i in igraci:
        for s in 'PSA':
            x = i['s'][s]
            mu0 = x.get('mu0')
            if mu0 and mu0 > 0:
                lo, hi = mu0 * (1 - m), mu0 * (1 + m)
                if not lo <= x['mu'] <= hi:
                    _postavi(x, min(hi, max(lo, x['mu'])))


def povratak(igraci, B, kod, dan, PAR=NOVO):
    tg = []
    for r in B.rows:
        if r['team'] == kod and r['dan'] < dan and r['g'] not in tg:
            tg.append(r['g'])
    if len(tg) < 4:
        return
    igrao = {i['k']: {r['g']: r for r in B.byk.get(i['k'], []) if r['dan'] < dan and r['team'] == kod} for i in igraci}
    povr = []
    for j in igraci:
        G = igrao[j['k']]
        if j['ne_igra'] or not G:
            continue
        mins = [r['min'] for r in G.values()]
        if sum(mins) / len(mins) < PAR['pov_min']:
            continue
        posle = 0
        for gg in reversed(tg):
            if gg in G:
                posle += 1
            else:
                break
        propustio = sum(1 for gg in tg if gg not in G)
        if 1 <= posle <= PAR['pov_max_posle'] and propustio >= 2 and propustio > posle - 1:
            povr.append((j, set(tg[len(tg) - posle:])))
    if not povr:
        return
    sa_g = set.intersection(*[s for _, s in povr])
    ko = [j['ime'] for j, _ in povr]
    kljucevi_povr = {j['k'] for j, _ in povr}
    lo_o, hi_o = PAR['pov_odnos']
    for i in igraci:
        if i['k'] in kljucevi_povr or i['ne_igra']:
            continue
        G = igrao[i['k']]
        sa = [G[gg] for gg in G if gg in sa_g]
        bez = [G[gg] for gg in G if gg not in sa_g]
        if not sa or len(bez) < 2:
            continue
        w = len(sa) / (len(sa) + PAR['pov_k'])
        sv = lambda L, s: sum(r[s] for r in L)
        m_sa = sv(sa, 'min') / len(sa)
        m_bez = sv(bez, 'min') / len(bez)
        m_sve = sv(sa, 'min') + sv(bez, 'min')
        m_staro = i['min']
        m_novo = m_staro if i.get('rucno_min') else (1 - w) * m_staro + w * m_sa
        info = dict(ko=ko, n=len(sa), w=round(w, 2), min_sa=round(m_sa, 1), min_bez=round(m_bez, 1), sa={}, bez={}, odnos={})
        for s in 'PSA':
            x = i['s'][s]
            r_sve = (sv(sa, s) + sv(bez, s)) / m_sve if m_sve else 0
            if r_sve > 0 and sv(sa, 'min') > 0:
                odnos = (sv(sa, s) + PAR['pov_c'][s]) / (r_sve * sv(sa, 'min') + PAR['pov_c'][s])
            else:
                odnos = 1.0
            odnos = min(hi_o, max(lo_o, odnos))
            mnoz = ((1 - w) + w * odnos) * (m_novo / m_staro if m_staro else 1)
            _postavi(x, x['mu'] * mnoz)
            x['rpm'] = round(x['mu'] / m_novo, 4) if m_novo else 0
            info['sa'][s] = round(sv(sa, s) / len(sa), 1)
            info['bez'][s] = round(sv(bez, s) / len(bez), 1)
            info['odnos'][s] = round(odnos, 2)
        i['min'] = round(m_novo, 1)
        i['povratak'] = info


def odsustvo(igraci, n_tim, PAR=NOVO):
    van = [j for j in igraci if j['ne_igra'] and j['min'] >= 12 and n_tim and j['n'] >= 0.5 * n_tim and j['odsutan'] < 3]
    akt = [i for i in igraci if not i['ne_igra'] and i['min'] >= 8]
    if not van or not akt:
        return
    dod = {i['k']: 0.0 for i in akt}
    for j in van:
        tez = {i['k']: i['min'] * BLIZINA.get((i['pos'], j['pos']), 0.6) for i in akt}
        zbir = sum(tez.values())
        for i in akt:
            dod[i['k']] += j['min'] * PAR['ods_udeo'] * tez[i['k']] / zbir
    if PAR.get('ods_dod_max') is not None:
        for k in dod:
            dod[k] = min(dod[k], PAR['ods_dod_max'])
    for _ in range(5):
        visak = 0.0
        for i in akt:
            if i['min'] + dod[i['k']] > PAR['ods_max_min']:
                visak += i['min'] + dod[i['k']] - PAR['ods_max_min']
                dod[i['k']] = max(0.0, PAR['ods_max_min'] - i['min'])
        slobodni = [i for i in akt if i['min'] + dod[i['k']] < PAR['ods_max_min'] - 0.01]
        if visak < 0.05 or not slobodni or PAR.get('ods_dod_max') is not None:
            break
        zbir = sum(i['min'] for i in slobodni)
        for i in slobodni:
            dod[i['k']] += visak * i['min'] / zbir
    # glavna opcija tima (najveće očekivanje poena među prisutnima): blago veći učinak po minutu za P i A
    glavni = max(akt, key=lambda i: i['s']['P']['mu'])['k'] if PAR.get('ods_glavni') else None
    ko = [j['ime'] for j in van]
    for i in akt:
        if i.get('rucno_min'):
            continue
        m_staro, m_novo = i['min'], i['min'] + dod[i['k']]
        f = m_novo / m_staro if m_staro else 1
        g = 1 + PAR['ods_glavni'] if i['k'] == glavni else 1
        if dod[i['k']] < 0.3 and g == 1:
            continue
        for s in 'PSA':
            x = i['s'][s]
            _postavi(x, x['mu'] * f * (g if s in 'PA' else 1))
        i['min'] = round(m_novo, 1)
        i['odsustvo'] = dict(ko=ko, min_staro=round(m_staro, 1), glavni=(i['k'] == glavni))


def prilagodi(igraci, B, kod, dan, n_tim, PAR=NOVO):
    zapamti_sirovo(igraci)
    if PAR is None:
        return
    povratak(igraci, B, kod, dan, PAR)
    odsustvo(igraci, n_tim, PAR)
    ogranici(igraci, PAR)
