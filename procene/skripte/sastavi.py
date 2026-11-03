"""Sastavi za utakmicu (12 prijavljenih igrača), kad ih Evroliga objavi.

  python3 procene/skripte/sastavi.py [--sati 6]

Za utakmice koje počinju u narednih --sati sati (ili su počele pre manje od 30 minuta) čita
https://api-live.euroleague.net/v3/competitions/E/seasons/E2026/games/N/stats
Pre utakmice je spisak prazan; kad se zapisnik otvori, tu je 12 prijavljenih igrača.
Igrač koji ima utakmice ove sezone a nije među prijavljenima dobija „ne igra (nije u sastavu)“ u tabli
i ne ulazi u predloge. Izlaz: procene/podaci/sastavi.json {gamecode: {tim: [ključevi igrača], 'at': vreme}}.
"""
import argparse, datetime as dt, json, os, sys, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, ucitaj, sacuvaj, utakmice, pn

URL = 'https://api-live.euroleague.net/v3/competitions/E/seasons/E2026/games/{}/stats'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--sati', type=float, default=6)
    a = ap.parse_args()
    put = os.path.join(PROCENE, 'podaci', 'sastavi.json')
    sast = ucitaj(put) if os.path.exists(put) else {}
    sada = dt.datetime.now(dt.timezone.utc)
    nadjeno = 0
    for u in utakmice():
        if not (sada - dt.timedelta(minutes=30) <= u['utc'] <= sada + dt.timedelta(hours=a.sati)):
            continue
        try:
            req = urllib.request.Request(URL.format(u['g']), headers={'User-Agent': 'curl/8.5.0'})
            d = json.loads(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print('greška', u['g'], e); continue
        zapis = {}
        for strana, kod in (('local', u['dom']), ('road', u['gost'])):
            igr = (d.get(strana) or {}).get('players') or []
            if len(igr) >= 8:          # pravi sastav, ne prazan ili delimičan
                zapis[kod] = sorted(pn(x['player']['person']['name']) for x in igr)
        if zapis:
            zapis['at'] = sada.isoformat(timespec='minutes')
            sast[str(u['g'])] = zapis
            nadjeno += 1
            print(f'sastav {u["g"]} {u["dom"]}-{u["gost"]}: ' + ', '.join(f'{k} {len(v)}' for k, v in zapis.items() if k != 'at'))
        else:
            print(f'sastav {u["g"]} {u["dom"]}-{u["gost"]}: još nije objavljen')
    sacuvaj(put, sast)
    print('sastava pronađeno', nadjeno)


if __name__ == '__main__':
    main()
