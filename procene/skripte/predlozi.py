"""Javni predlozi po kolu: preko i ispod, poeni, skokovi i asistencije.

  python3 procene/skripte/predlozi.py --kolo 11      (posle tabla.py --kolo 11)
  python3 procene/skripte/predlozi.py                 (samo osvežava ishode i stranicu)

Pravilo (procene/skripte/spajanje.py):
  - za svaku granicu spojena verovatnoća (model + kvote, podešeno prema ishodima), ista za obe strane
  - strana ulazi ako je spojena verovatnoća najmanje P_MIN, prednost (verovatnoća × kvota − 1) najmanje EV_MIN
    i kvota najmanje KVOTA_MIN
  - igrač sa bar 3 utakmice ove sezone, odigrao sve 3 poslednje utakmice svog tima, nije označen da ne igra
  - jedan predlog po igraču: najizglednija strana i granica (pa veća prednost)
Predlozi za utakmicu se zaključavaju kad utakmica počne. Ishodi se upisuju iz baza/rows.json.
Izlaz: procene/predlozi/kolo<N>.json i procene/javno/predlozi.html (iz procene/javno/sablon.html).
"""
import argparse, datetime as dt, glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from model import Baza
from zajedno import PROCENE, BG, ucitaj, sacuvaj
import spajanje

IME_KL = {'admiral': 'Admiral', 'maxbet': 'MaxBet', 'mozzart': 'Mozzart', 'soccerbet': 'Soccerbet'}


def izaberi(tabla, w):
    kand = []
    for u in tabla['utakmice']:
        if u['pocela']:
            continue
        for st in u['strane']:
            for i in st['igraci']:
                if i['ne_igra'] or i['odsutan'] > 0 or i['n'] < 3:
                    continue
                for s in 'PSA':
                    for z in i['s'][s]['linije']:
                        p = spajanje.preko(w, s, z['pm'], z['tr'])
                        osn = dict(id=(u['g'], i['k']), g=u['g'], dan=u['dan'], vreme=u['vreme'], k=i['k'], ime=i['ime'],
                                   tim=st['tim'], prot=st['prot'], s=s, l=z['l'], kl=z['kl'], pm=z['pm'], tr=z['tr'],
                                   mu=i['s'][s]['mu'], min=i['min'])
                        kand.append(dict(osn, strana='o', pp=p, ev=p * z['o'] - 1, k_=z['o']))
                        kand.append(dict(osn, strana='u', pp=1 - p, ev=(1 - p) * z['u'] - 1, k_=z['u']))
    for c in kand:
        c['k'], c['igrac'] = c['k_'], c['k']          # izbor() gleda kvotu u 'k'
    out = []
    for c in spajanje.izbor(kand):
        c['kvota'] = c.pop('k'); c['k'] = c.pop('igrac'); c.pop('k_'); c.pop('id')
        c['pp'] = round(c['pp'], 3); c['ev'] = round(c['ev'], 3)
        out.append(c)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    sp = ucitaj(os.path.join(PROCENE, 'spajanje.json'))
    folder = os.path.join(PROCENE, 'predlozi')
    os.makedirs(folder, exist_ok=True)
    sada = dt.datetime.now(dt.timezone.utc).astimezone(BG).strftime('%d.%m.%Y. %H:%M')
    if a.kolo:
        tabla = ucitaj(os.path.join(PROCENE, 'tabla', f'kolo{a.kolo}.json'))
        put = os.path.join(folder, f'kolo{a.kolo}.json')
        st = ucitaj(put) if os.path.exists(put) else {'kolo': a.kolo, 'predlozi': []}
        pocele = {u['g'] for u in tabla['utakmice'] if u['pocela']}
        zadrzi = [p for p in st['predlozi'] if p['g'] in pocele]          # zaključani
        novi = izaberi(tabla, sp['w'])
        for p in novi:
            p['upisano'] = sada
        st['predlozi'] = zadrzi + novi
        st['osvezeno'] = sada
        st['utakmice'] = [dict(g=u['g'], dom=u['dom'], gost=u['gost'], vreme=u['vreme'], dan=u['dan'],
                               ponude=sorted(u['snimci'].keys())) for u in tabla['utakmice']]
        sacuvaj(put, st)
        print(f'kolo {a.kolo}: predloga {len(st["predlozi"])} (zaključanih {len(zadrzi)}, novih {len(novi)}, '
              f'preko {sum(p["strana"] == "o" for p in novi)})')

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
                y = r[p['s']]
                p['ishod'] = y
                p['prosao'] = (y > p['l']) if p.get('strana') == 'o' else (y < p['l'])
            elif p['g'] in igrane:
                p['ishod'] = None; p['prosao'] = None; p['nije_igrao'] = True   # ulog se vraća
        sacuvaj(f, st)
        kola.append(st)

    stranica = dict(osvezeno=sada, pravilo=sp['pravilo'], kladionice=IME_KL, kola=kola, unazad=sp['test'])
    sab = open(os.path.join(PROCENE, 'javno', 'sablon.html'), encoding='utf-8').read()
    js = json.dumps(stranica, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    with open(os.path.join(PROCENE, 'javno', 'predlozi.html'), 'w', encoding='utf-8') as f:
        f.write(sab.replace('__PODACI__', js))
    print('stranica: procene/javno/predlozi.html, kola', [k['kolo'] for k in kola])


if __name__ == '__main__':
    main()
