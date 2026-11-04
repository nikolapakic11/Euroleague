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
    # utakmice sačuvane dok je zapisnik još bio „uživo“ osvežavaju se dok ne postanu konačne (najduže 4 sata od početka)
    put_p = os.path.join(PROCENE, 'podaci', 'dopuna_privremeno.json')
    privremeno = set(ucitaj(put_p)) if os.path.exists(put_p) else set()
    sada = dt.datetime.now(dt.timezone.utc)
    sve = utakmice()
    pocetak = {u['g']: u['utc'] for u in sve}
    privremeno = {g for g in privremeno if g not in u_bazi and g in pocetak and pocetak[g] > sada - dt.timedelta(hours=4)}
    dop = [r for r in dop if r['g'] not in privremeno]
    u_dopuni = {r['g'] for r in dop}
    POS = pozicije()
    gotove = [u for u in sve if u['utc'] < sada - dt.timedelta(hours=1, minutes=45)
              and u['g'] not in u_bazi and u['g'] not in u_dopuni]
    novo = 0
    for u in gotove:
        try:
            d = zapisnik(u['g'])
        except Exception as e:
            print('greška', u['g'], e); continue
        if not d or not d.get('Stats') or not any(s['PlayersStats'] for s in d['Stats']):
            continue
        # utakmica je završena kad zapisnik nije „uživo“, ili kad je kraj vidljiv (poslednja četvrtina ili produžetak
        # zatvoren i rezultat nije nerešen) posle bar 1:45 od početka
        kraj = d.get('EndOfQuarter') or []
        zatvoreno = len(kraj) == 2 and all(k.get('Quarter4') is not None for k in kraj)
        rez = [s['totr']['Points'] for s in d['Stats']]
        uzivo = bool(d.get('Live'))
        if uzivo and not (zatvoreno and rez[0] != rez[1]) and u['utc'] > sada - dt.timedelta(hours=2, minutes=30):
            continue
        r = redovi(u['g'], d, u, POS)
        if len({x['team'] for x in r}) == 2:
            dop += r; novo += 1
            if uzivo:
                privremeno.add(u['g'])
            else:
                privremeno.discard(u['g'])
            # ceo zapisnik (za statistiku timova i igrača, procene/skripte/statistika.py)
            os.makedirs(os.path.join(PROCENE, 'podaci', 'zapisnici'), exist_ok=True)
            sacuvaj(os.path.join(PROCENE, 'podaci', 'zapisnici', f"{u['g']}.json"), d, kompaktno=True)
        time.sleep(0.3)
    sacuvaj(put, dop, kompaktno=True)
    sacuvaj(put_p, sorted(privremeno))
    print(f'dopuna: novih utakmica {novo}, ukupno u dopuni {len({r["g"] for r in dop})}')


if __name__ == '__main__':
    main()
