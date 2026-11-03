"""Prošla sezona (E2025) kao polazna procena za igrače.

  python3 procene/skripte/prosla_sezona.py <folder sa bs_N.json>

Zapisnici prošle sezone se preuzimaju sa
  https://live.euroleague.net/api/Boxscore?gamecode=N&seasoncode=E2025
u privremeni folder (ne u repozitorijum). Ova skripta od njih pravi
procene/podaci/e2025_igraci.json: po igraču utakmice, minuti i zbir P, S, A, poslednji tim.
"""
import glob, json, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, pn, sacuvaj


def main(folder):
    igr = {}
    for f in sorted(glob.glob(os.path.join(folder, 'bs_*.json')), key=lambda x: int(re.findall(r'\d+', os.path.basename(x))[0])):
        gc = int(re.findall(r'\d+', os.path.basename(f))[0])
        try:
            d = json.load(open(f))
        except Exception:
            continue
        for s in d.get('Stats', []):
            for p in s.get('PlayersStats', []):
                mm = p.get('Minutes')
                if not mm or ':' not in mm:
                    continue
                a, b = mm.split(':')
                m = int(a) + int(b) / 60
                if m <= 0:
                    continue
                k = pn(p['Player'])
                x = igr.setdefault(k, {'n': 0, 'min': 0.0, 'P': 0, 'S': 0, 'A': 0, 'tim': None, 'g': 0})
                x['n'] += 1; x['min'] += m; x['P'] += p['Points']; x['S'] += p['TotalRebounds']; x['A'] += p['Assistances']
                if gc >= x['g']:
                    x['g'] = gc; x['tim'] = p['Team'].strip()
    for x in igr.values():
        x['min'] = round(x['min'], 1)
        del x['g']
    out = {'sezona': 'E2025', 'izvor': 'live.euroleague.net Boxscore, sve odigrane utakmice', 'igraci': igr}
    sacuvaj(os.path.join(PROCENE, 'podaci', 'e2025_igraci.json'), out, kompaktno=True)
    print('igrača', len(igr))


if __name__ == '__main__':
    main(sys.argv[1])
