"""Stalno doterivanje logike (od 13.11.2026, Nikola: „konstantno moramo da gledamo da povećamo uspešnost“).

  python3 spoj/posle_kola.py            # posle svakog dana sa utakmicama (ujutru)

Redom, bez ručnog rada:
  1. preuzme zapisnike odigranih utakmica kojih nema u baza/zapisnici (live.euroleague.net)
  2. baza: build.py (rows.json) i ctx2.py
  3. spoj: provera.py, analiza/prep.py, tezine.py (težine spoja ponovo naučene na svim ishodima)
  4. analiza/an3.py: rangiranje, novi signali, pravila za sajt (izveštaj u spoj/analiza/poslednja_provera.txt)
  5. učinak sajta po pravilu od 13.11. (predlozi sa spoj=True) i upozorenje kad padne ispod očekivanog
Ishodi tiketa i sajta se upisuju posebno (minusi/uzivo/upis_rezultata.py, procene/skripte/dan.py).
"""
import glob, json, os, subprocess, sys, urllib.request

KOREN = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(KOREN)
PY = sys.executable


def run(*a):
    r = subprocess.run([PY] + list(a), capture_output=True, text=True)
    izl = (r.stdout + r.stderr).strip().splitlines()
    print(f"  {' '.join(a)}: {izl[-1] if izl else ''}")
    return r.stdout


g = json.load(open('baza/games.json'))
G = g['data'] if isinstance(g, dict) else g
ima = {int(os.path.basename(f)[:-5]) for f in glob.glob('baza/zapisnici/*.json')}
novi = []
for u in G:
    kod = u['gameCode']
    if kod in ima or u['utcDate'][:10] > __import__('datetime').date.today().isoformat():
        continue
    try:
        req = urllib.request.Request(f'https://live.euroleague.net/api/Boxscore?gamecode={kod}&seasoncode=E2026', headers={'User-Agent': 'curl/8.5.0'})
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
    except Exception:
        continue
    if d.get('Stats') and not d.get('Live'):
        json.dump(d, open(f'baza/zapisnici/{kod}.json', 'w'))
        novi.append(kod)
print('1. novi zapisnici:', novi or 'nema')
print('2. baza'); run('baza/skripte/build.py'); run('baza/skripte/ctx2.py', 'baza/ctx2.json')
print('3. spoj'); run('spoj/provera.py'); run('spoj/analiza/prep.py'); print(run('spoj/tezine.py').strip().splitlines()[-1])
print('4. analiza')
out = run('spoj/analiza/an3.py')
open('spoj/analiza/poslednja_provera.txt', 'w').write(out)
for red in out.splitlines():
    if 'ISPOD (top4 po verovatnoći' in red or 'SAJT ukupno' in red or 'PREKO (P/A' in red:
        print('   ', red.strip()[:200])
print('5. sajt po pravilu od 13.11.')
U = {'u': [0, 0], 'o': [0, 0]}
for f in glob.glob('procene/predlozi/kolo*.json'):
    for p in json.load(open(f))['predlozi']:
        if p.get('spoj') and p.get('prosao') is not None and not p.get('povucen'):
            U[p['strana']][0] += bool(p['prosao']); U[p['strana']][1] += 1
for st, ime, ocek in (('u', 'MINUS', .65), ('o', 'PLUS', .58)):
    h, n = U[st]
    print(f"   {ime}: {h}/{n}" + (f" = {h / n:.0%} (očekivano ~{ocek:.0%})" if n else '') +
          ('  <- ISPOD OČEKIVANOG, preispitati pravilo' if n >= 20 and h / n < ocek - 0.08 else ''))
