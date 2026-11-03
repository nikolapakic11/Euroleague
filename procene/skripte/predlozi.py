"""Javni predlozi po kolu.

  python3 procene/skripte/predlozi.py --kolo 11      (posle tabla.py --kolo 11)
  python3 procene/skripte/predlozi.py                 (samo osvežava ishode i stranicu)

Pravilo (izabrano na proveri unazad, oktobar 2026):
  - samo ISPOD, samo skokovi i asistencije
  - prednost modela (verovatnoća ispod × kvota − 1) najmanje 20%, kvota najmanje 1,50
  - igrač sa bar 3 utakmice ove sezone, odigrao sve 3 poslednje utakmice svog tima, nije označen da ne igra
  - jedan predlog po igraču: granica i kladionica sa najvećom prednošću
Predlozi za utakmicu se zaključavaju kad utakmica počne. Ishodi se upisuju iz baza/rows.json.
Izlaz: procene/predlozi/kolo<N>.json i procene/javno/predlozi.html (iz procene/javno/sablon.html).
"""
import argparse, datetime as dt, glob, json, math, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from model import Baza
from zajedno import PROCENE, BG, ucitaj, sacuvaj

PRAG = 0.20
KVOTA_MIN = 1.50
STAVKE = ('S', 'A')
IME_S = {'P': 'poeni', 'S': 'skokovi', 'A': 'asistencije'}
IME_KL = {'admiral': 'Admiral', 'maxbet': 'MaxBet', 'mozzart': 'Mozzart', 'soccerbet': 'Soccerbet'}


def izaberi(tabla):
    out = []
    for u in tabla['utakmice']:
        if u['pocela']:
            continue
        for st in u['strane']:
            for i in st['igraci']:
                if i['ne_igra'] or i['odsutan'] > 0 or i['n'] < 3:
                    continue
                naj = None
                for s in STAVKE:
                    for z in i['s'][s]['linije']:
                        pu = 1 - z['pm']
                        ev = pu * z['u'] - 1
                        if ev >= PRAG and z['u'] >= KVOTA_MIN and (naj is None or ev > naj['ev']):
                            naj = dict(g=u['g'], dan=u['dan'], vreme=u['vreme'], k=i['k'], ime=i['ime'], tim=st['tim'],
                                       prot=st['prot'], s=s, l=z['l'], kl=z['kl'], kvota=z['u'], pu=round(pu, 3),
                                       ev=round(ev, 3), mu=i['s'][s]['mu'], min=i['min'])
                if naj:
                    out.append(naj)
    return out


def provera_unazad():
    """Isto pravilo na proveri unazad (procene/provera/granice.json), po kolu."""
    p = os.path.join(PROCENE, 'provera', 'granice.json')
    if not os.path.exists(p):
        return None
    best = {}
    for r in ucitaj(p):
        if r['s'] not in STAVKE:
            continue
        pu = 1 - r['pm']; ev = pu * r['u'] - 1
        if ev >= PRAG and r['u'] >= KVOTA_MIN:
            k = (r['dan'], r['k'])
            if k not in best or ev > best[k][1]:
                best[k] = (r, ev)
    po_kolu = {}
    for r, ev in best.values():
        x = po_kolu.setdefault(r['kolo'], [0, 0, 0.0])
        x[0] += 1; x[1] += r['preko'] == 0; x[2] += (r['u'] - 1) if r['preko'] == 0 else -1
    kola = [dict(kolo=k, n=v[0], prosao=v[1], dobit=round(v[2], 2)) for k, v in sorted(po_kolu.items())]
    n = sum(k['n'] for k in kola)
    return dict(kola=kola, n=n, prosao=sum(k['prosao'] for k in kola), dobit=round(sum(k['dobit'] for k in kola), 2),
                izvor='Admiral i MaxBet, 8.10. do 30.10.2026, jedna kladionica po danu')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    folder = os.path.join(PROCENE, 'predlozi')
    os.makedirs(folder, exist_ok=True)
    sada = dt.datetime.now(dt.timezone.utc).astimezone(BG).strftime('%d.%m.%Y. %H:%M')
    if a.kolo:
        tabla = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
        put = os.path.join(folder, f'kolo{a.kolo}.json')
        st = ucitaj(put) if os.path.exists(put) else {'kolo': a.kolo, 'predlozi': []}
        pocele = {u['g'] for u in tabla['utakmice'] if u['pocela']}
        zadrzi = [p for p in st['predlozi'] if p['g'] in pocele]          # zaključani
        novi = izaberi(tabla)
        for p in novi:
            p['upisano'] = sada
        st['predlozi'] = zadrzi + novi
        st['osvezeno'] = sada
        st['utakmice'] = [dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'],
                               ponude=sorted(u['snimci'].keys())) for u in tabla['utakmice']]
        sacuvaj(put, st)
        print(f'kolo {a.kolo}: predloga {len(st["predlozi"])} (zaključanih {len(zadrzi)}, novih {len(novi)})')

    # ishodi za sva kola
    B = Baza()
    ish = {(r['g'], r['k']): r for r in B.rows}
    igrane = {r['g'] for r in B.rows}
    kola = []
    for f in sorted(glob.glob(os.path.join(folder, 'kolo*.json')), key=lambda x: int(''.join(c for c in os.path.basename(x) if c.isdigit()))):
        st = ucitaj(f)
        for p in st['predlozi']:
            r = ish.get((p['g'], p['k']))
            if r:
                p['ishod'] = r[p['s']]; p['prosao'] = r[p['s']] < p['l']
            elif p['g'] in igrane:
                p['ishod'] = None; p['prosao'] = None; p['nije_igrao'] = True   # vraća se ulog
        sacuvaj(f, st)
        kola.append(st)

    stranica = dict(osvezeno=sada, pravilo=dict(prag=PRAG, kvota_min=KVOTA_MIN, stavke=[IME_S[s] for s in STAVKE]),
                    kladionice=IME_KL, kola=kola, unazad=provera_unazad())
    sab = open(os.path.join(PROCENE, 'javno', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(stranica, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'javno', 'predlozi.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    print('stranica: procene/javno/predlozi.html, kola', [k['kolo'] for k in kola])


if __name__ == '__main__':
    main()
