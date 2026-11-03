"""Dopuna statistike: utakmice koje su završene a još nisu u baza/rows.json.

  python3 procene/skripte/dopuna.py

Razgovor za minuse ažurira baza/rows.json posle kola; da procene ne bi čekale, ova skripta
povlači zapisnike završenih utakmica direktno (isti izvor i isti postupak kao baza/skripte/build.py)
i čuva ih u procene/podaci/dopuna.json. model.Baza učitava rows.json + dopunu (bez duplikata).
"""
import datetime as dt, glob, json, os, sys, time, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, PROCENE, ucitaj, sacuvaj, utakmice, pn

URL = 'https://live.euroleague.net/api/Boxscore?gamecode={}&seasoncode=E2026'


def zapisnik(gc):
    req = urllib.request.Request(URL.format(gc), headers={'User-Agent': 'curl/8.5.0'})
    b = urllib.request.urlopen(req, timeout=30).read()
    return json.loads(b) if b.strip() else None


def pozicije():
    pos = {}
    for f in glob.glob(os.path.join(BAZA, 'rosteri', '*.json')):
        for x in ucitaj(f):
            if x.get('type') == 'J' and x.get('person'):
                pos[pn(x['person']['name'])] = x.get('positionName') or ''
    return pos


def grp(p):
    return 'G' if p == 'Guard' else 'C' if p == 'Center' else 'F' if p == 'Forward' else '?'


def redovi(gc, d, u, POS):
    out = []
    teams = [s['PlayersStats'][0]['Team'] if s['PlayersStats'] else None for s in d['Stats']]
    for s in d['Stats']:
        for p in s['PlayersStats']:
            mm = p['Minutes']
            if not mm or ':' not in mm:
                continue
            a, b = mm.split(':')
            m = int(a) + int(b) / 60
            if m <= 0:
                continue
            tm = p['Team'].strip()
            opp = [t for t in teams if t and t.strip() != tm]
            k = pn(p['Player'])
            out.append(dict(g=gc, r=u['r'], d=u['lok'], team=tm, opp=opp[0].strip() if opp else '', k=k, name=p['Player'],
                            min=m, P=p['Points'], S=p['TotalRebounds'], A=p['Assistances'], st=p.get('IsStarter', 0),
                            pos=grp(POS.get(k, ''))))
    return out


def main():
    rows = ucitaj(os.path.join(BAZA, 'rows.json'))
    u_bazi = {r['g'] for r in rows}
    put = os.path.join(PROCENE, 'podaci', 'dopuna.json')
    dop = ucitaj(put) if os.path.exists(put) else []
    dop = [r for r in dop if r['g'] not in u_bazi]          # baza je stigla, dopuna više ne treba
    u_dopuni = {r['g'] for r in dop}
    sada = dt.datetime.now(dt.timezone.utc)
    POS = pozicije()
    gotove = [u for u in utakmice() if u['utc'] < sada - dt.timedelta(hours=2, minutes=30)
              and u['g'] not in u_bazi and u['g'] not in u_dopuni]
    novo = 0
    for u in gotove:
        try:
            d = zapisnik(u['g'])
        except Exception as e:
            print('greška', u['g'], e); continue
        if not d or not d.get('Stats') or not any(s['PlayersStats'] for s in d['Stats']):
            continue
        # utakmica mora biti završena: oba tima imaju igrače sa minutima
        r = redovi(u['g'], d, u, POS)
        if len({x['team'] for x in r}) == 2:
            dop += r; novo += 1
        time.sleep(0.3)
    sacuvaj(put, dop, kompaktno=True)
    print(f'dopuna: novih utakmica {novo}, ukupno u dopuni {len({r["g"] for r in dop})}')


if __name__ == '__main__':
    main()
