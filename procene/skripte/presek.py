"""Presek za dan pre objave (konsultacija sa Nikolom, odluka 6.11.2026): šta bi se objavilo i zašto.

  python3 procene/skripte/presek.py [--dan 2026-11-06] [--kolo 10]

Čita tablu (procene/tabla/kolo<N>.json, posle tabla.py) i bira predloge za dan istim pravilom kao predlozi.py
(izbor_dana), bez ikakve objave. Ispisuje: odsutne i upitne po timu, izabrane predloge sa očekivanjem, prosekom,
poslednjih 5, minutima, kvotama svih kladionica i formom, pa najbliže PLUS i MINUS ispod praga.
"""
import argparse, datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import predlozi as PR
from model import Baza
from zajedno import PROCENE, BG, ucitaj

SN = {'P': 'poeni', 'S': 'skokovi', 'A': 'asist.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dan', default=dt.datetime.now(BG).date().isoformat())
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    if a.kolo is None:
        import glob
        for f in sorted(glob.glob(os.path.join(PROCENE, 'tabla', 'kolo*.json'))):
            T = ucitaj(f)
            if any(u['dan'] == a.dan for u in T['utakmice']):
                a.kolo = T['kolo']
    T = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
    B = Baza()
    kand, igr = [], {}
    print(f'Presek za {a.dan} (kolo {a.kolo}, tabla {T["napravljeno"]}, podaci do {T["podaci_do"]})\n')
    for u in T['utakmice']:
        if u['dan'] != a.dan:
            continue
        print(f"{u['dom']}–{u['gost']} {u['vreme']}  snimci: {', '.join(f'{k} {v[11:16]}' for k, v in (u.get('snimci') or {}).items())}")
        for st in u['strane']:
            van = [f"{x['ime']} ({x['zasto']})" for x in st.get('nedostaju', [])]
            upit = [i['ime'] for i in st['igraci'] if i.get('upitan')]
            if van or upit:
                print(f"   {st['tim']}: " + ('bez MINUS-a, ne igra: ' + ', '.join(van) if van else '') + (('; ' if van else '') + 'upitni: ' + ', '.join(upit) if upit else ''))
            for i in st['igraci']:
                for s in 'PSA':
                    x = i['s'][s]
                    igr[(u['g'], i['k'], s)] = (u, st, i, x)
                    pr = x.get('pred')
                    if pr:
                        kand.append(dict(g=u['g'], dan=u['dan'], k=i['k'], ime=i['ime'], tim=st['tim'], s=s, strana=pr['strana'],
                                         l=pr['l'], kl=pr['kl'], kvota=pr['kvota'], pp=pr['pp'], nivo=pr['nivo']))
    izab = PR.izbor_dana([dict(c) for c in kand], B)
    print(f'\nPREDLOZI ({len(izab)}; pravilo: prag {PR.DAN_PRAG:.0%}, najmanje {PR.DAN_NAJMANJE}, najviše {PR.DAN_MAX}, PLUS do {PR.DAN_PLUS} od {PR.DAN_PLUS_PRAG:.0%})')
    for p in izab:
        u, st, i, x = igr[(p['g'], p['k'], p['s'])]
        o = p['strana'] == 'o'
        kn = ', '.join(f"{z['kl']} {z['l']} {z['o'] if o else z['u']}" for z in x['linije'] if z.get('m', 1))
        dod = []
        if i.get('povratak'):
            dod.append('povratak ' + ', '.join(i['povratak']['ko']))
        if i.get('odsustvo'):
            dod.append('odsustvo ' + ', '.join(i['odsustvo']['ko']))
        print(f"  {p['pp']:.0%} {'PLUS ' if o else 'MINUS'} {p['ime']} ({p['tim']}–{st['prot']}) {SN[p['s']]} {'preko' if o else 'ispod'} {p['l']} @ {p['kvota']} {p['kl']}"
              f"\n       očekivano {x['mu']} (raspon {x['q'][1]}–{x['q'][3]}), prosek {x['pros']}, posl. 5 {x['posl']}, min {i['min']}, forma {p['forma'][0]}/{p['forma'][1]}"
              f"\n       kladionice: {kn}" + (f"\n       {'; '.join(dod)}" if dod else ''))
    van_izb = sorted([c for c in kand if not any(c['k'] == q['k'] and c['s'] == q['s'] for q in izab)], key=lambda c: -c['pp'])
    for strana, ime in (('o', 'PLUS'), ('u', 'MINUS')):
        L = [c for c in van_izb if c['strana'] == strana][:5]
        if L:
            print(f'\nNajbliži {ime} ispod praga: ' + '; '.join(f"{c['ime']} {SN[c['s']]} {c['l']} {c['pp']:.0%}" for c in L))


if __name__ == '__main__':
    main()
