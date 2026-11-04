"""Ceo dnevni posao za procene, jednom komandom (koriste ga i zakazani zadaci).

  python3 procene/skripte/dan.py [--jutro]

Redom:
  1. dopuna.py      završene utakmice koje još nisu u baza/rows.json; statistika.py statistika timova i igrača
  2. sastavi.py     objavljeni sastavi za utakmice u narednih 6 sati; povrede.py zvanični izveštaj o povredama
  3. soccerbet.py   snimak ponude, ako danas ima utakmica koje nisu počele
  4. --jutro: provera.py i spajanje.py (koeficijenti se osvežavaju sa novim ishodima) i domace.py (u pozadini, bez prikaza)
  5. tabla.py --dnevnik i predlozi.py za tekuće kolo (i kolo današnjih utakmica, ako je drugo)
  6. predlozi.py (ishodi svih kola) i dnevnik.py za kola sa ishodima
  7. procene/tabla/aktuelno.html = tabla tekućeg kola
Na kraju ispisuje pregled: šta je urađeno, koje ponude postoje za danas i šta treba ručno.
"""
import argparse, datetime as dt, glob, os, shutil, subprocess, sys
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import BAZA, PROCENE, BG, KOREN, utakmice, ucitaj, kljuc_snimka, rokovi

SK = os.path.dirname(os.path.abspath(__file__))


def pokreni(*args):
    print('$', ' '.join(args), flush=True)
    r = subprocess.run([sys.executable, os.path.join(SK, args[0])] + list(args[1:]), cwd=KOREN,
                       capture_output=True, text=True)
    izlaz = (r.stdout or '').strip().splitlines()
    for red in izlaz[-8:]:
        print('  ' + red)
    if r.returncode != 0:
        print('  GREŠKA:', (r.stderr or '').strip().splitlines()[-1:] or r.returncode)
    return r.returncode == 0, izlaz


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jutro', action='store_true', help='osveži i proveru i spajanje')
    a = ap.parse_args()
    sada = dt.datetime.now(dt.timezone.utc)
    danas = sada.astimezone(BG).date().isoformat()
    sve = utakmice()
    danasnje = [u for u in sve if u['dan'] == danas]
    nepocete_danas = [u for u in danasnje if u['utc'] > sada]
    buduce = sorted([u for u in sve if u['utc'] > sada - dt.timedelta(hours=3)], key=lambda u: u['utc'])
    tekuce = buduce[0]['r'] if buduce else max(u['r'] for u in sve)
    kola = sorted({tekuce} | {u['r'] for u in danasnje})
    pregled = [f'Dan {danas}: utakmica danas {len(danasnje)} (nije počelo {len(nepocete_danas)}), tekuće kolo {tekuce}']

    pokreni('dopuna.py')
    pokreni('statistika.py')
    pokreni('sastavi.py', '--sati', '6')
    ok, iz = pokreni('povrede.py')
    pregled.append('Povrede: ' + (iz[-1] if iz else 'bez izlaza'))
    if nepocete_danas:
        ok, iz = pokreni('soccerbet.py')
        pregled.append('Soccerbet: ' + (iz[0] if iz else 'bez izlaza'))
    if a.jutro:
        pokreni('provera.py')
        pokreni('spajanje.py')
        ok, iz = pokreni('domace.py')
        pregled.append('Domaće utakmice: ' + (iz[-1] if iz else 'bez izlaza'))
    for k in kola:
        ok, iz = pokreni('tabla.py', '--kolo', str(k), '--dnevnik')
        if ok:
            ok2, iz2 = pokreni('predlozi.py', '--kolo', str(k))
            pregled += [f'Kolo {k}: ' + r for r in iz2 if r.startswith('kolo')]
    pokreni('predlozi.py')
    for f in sorted(glob.glob(os.path.join(PROCENE, 'dnevnik', 'kolo*.json'))):
        k = ''.join(c for c in os.path.basename(f) if c.isdigit())
        pokreni('dnevnik.py', '--kolo', k)
    src = os.path.join(PROCENE, 'tabla', f'kolo{tekuce}.html')
    if os.path.exists(src):
        shutil.copyfile(src, os.path.join(PROCENE, 'tabla', 'aktuelno.html'))
        pregled.append(f'Tabla: procene/tabla/aktuelno.html = kolo {tekuce}')

    # ponude za danas po kladionici
    if danasnje:
        ima = []
        for kl in ('admiral', 'maxbet', 'mozzart', 'soccerbet'):
            n = len(glob.glob(os.path.join(BAZA, 'ponude', kl, f'*{danas}*.json')))
            ima.append(f'{kl} {n}')
        pregled.append('Snimci ponude za danas: ' + ', '.join(ima))
        # ručne kladionice: za konačne predloge (rok iz zajedno.rokovi) treba snimak posle 14:00
        sad_bg = sada.astimezone(BG)
        R = rokovi(sve)
        objava, rok = R[danasnje[0]['g']]
        pregled.append(f'Objava od {objava.strftime("%H:%M")}, konačni predlozi u {rok.strftime("%H:%M")}'
                       + (' (još nije objava: predlozi za danas se ne prikazuju)' if sad_bg < objava else ''))
        rucno, stari = [], []
        for kl in ('admiral', 'maxbet', 'mozzart'):
            F = sorted(glob.glob(os.path.join(BAZA, 'ponude', kl, f'*{danas}*.json')), key=kljuc_snimka)
            if not F:
                rucno.append(kl); continue
            try:
                at = dt.datetime.fromisoformat(ucitaj(F[-1]).get('at', '').replace('Z', '+00:00')).astimezone(BG)
            except Exception:
                continue
            if sad_bg < rok and at.strftime('%H:%M') < '14:00':
                stari.append(f'{kl} ({at.strftime("%H:%M")})')
        if (rucno or stari) and nepocete_danas:
            prva = min(u['utc'] for u in nepocete_danas).astimezone(BG).strftime('%H:%M')
            delovi = ([f'nema snimka za {", ".join(rucno)}'] if rucno else []) + ([f'osveži posle 14:00: {", ".join(stari)}'] if stari else [])
            pregled.append(f'RUČNO: {"; ".join(delovi)}; konačni predlozi u {rok.strftime("%H:%M")}, prva utakmica u {prva}.')
    print('\n=== PREGLED ===')
    print('\n'.join(pregled))


if __name__ == '__main__':
    main()
