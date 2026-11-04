"""Zvanični izveštaj Evrolige o povredama za tekuće kolo, preko Eurohoops prenosa (zvanični portal odbija automatski pristup).

  python3 procene/skripte/povrede.py            tekuće kolo
  python3 procene/skripte/povrede.py --kolo 10

Eurohoops za svako kolo objavi izveštaj (i dopune pred drugi dan kola). Skripta nađe te članke na
https://www.eurohoops.net/en/euroleague/ (naslov sadrži „injury report“ i „round N“), pročita ih po utakmicama i timovima
i za svakog pomenutog igrača odredi stanje iz rečenice:
  van     van igre (povreda, „out“, „ruled out“, „last played“, „yet to play“, „absentee“ ...)
  upitan  neizvestan („questionable“, „game-time decision“, „doubtful“ ...)
  igra    dostupan („available“, „cleared“, „returns“ ...); i ceo tim kad piše „full roster available“
Kasniji članak menja stanje iz ranijeg. Izlaz: procene/podaci/povrede.json
  {kolo, at, izvori: [url], igraci: {ključ: {tim, stanje, tekst}}, timovi: {kod: {pun_sastav, bez_izvestaja}}}
Koristi ga tabla.py: van igre = ne igra (i računa se kao odsutan saigrač), upitan = bez predloga za tog igrača,
igra = ne računa se kao odsutan čak i kad ga nema u ponudi kladionica.
"""
import argparse, datetime as dt, html, json, os, re, sys, unicodedata, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from zajedno import PROCENE, BAZA, BG, ucitaj, sacuvaj, tim, utakmice, nk

LISTA = 'https://www.eurohoops.net/en/euroleague/'
ZAG = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64)'}

R_IGRA = re.compile(r'\b(available|cleared|will play|returns?|returned|returning|is back|back in action|expected to play|ready to play|good to go)\b', re.I)
R_NIJE = re.compile(r'\b(unavailable|not available|not be available|won.t be available)\b', re.I)
R_UPITAN = re.compile(r'\b(questionable|game.time decision|gtd|doubtful|uncertain|day.to.day|in doubt|50.50|probable)\b', re.I)
R_VAN = re.compile(r'\b(out|ruled out|will miss|misses|miss|sidelined|injur\w*|sprain\w*|ruptur\w*|tear|torn|surgery|fractur\w*|strain\w*|'
                   r'last played|has not featured|hasn.t featured|has not played|yet to play|not on the \w* ?roster|absentee|suspend\w*|'
                   r'concussion|illness|sick|knee|ankle|hamstring|calf|shoulder|foot|back pain)\b', re.I)


def get(url):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=ZAG), timeout=30) as r:
            return r.read().decode('utf-8', 'replace')
    except Exception as e:
        print('ne mogu:', url, e)
        return ''


def tekst_linije(h):
    h = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', h, flags=re.S)
    h = re.sub(r'<[^>]+>', '\n', h)
    h = html.unescape(h)
    return [re.sub(r'\s+', ' ', x).strip() for x in h.split('\n') if x.strip()]


def stanje(recenica):
    if R_NIJE.search(recenica):
        return 'van'
    if R_IGRA.search(recenica):
        return 'igra'
    if R_UPITAN.search(recenica):
        return 'upitan'
    if R_VAN.search(recenica):
        return 'van'
    return None


def igraci_tima(kod):
    """ključ -> lista reči imena (bez kvačica), za igrače koji su igrali za tim ove sezone ili su na rosteru."""
    from model import Baza
    out = {}
    B = igraci_tima.B = getattr(igraci_tima, 'B', None) or Baza()
    for k, G in B.byk.items():
        if G and G[-1]['team'] == kod:
            out[k] = k.split()
    p = os.path.join(BAZA, 'rosteri', f'{kod}.json')
    if os.path.exists(p):
        for x in ucitaj(p):
            if x.get('type') == 'J' and x.get('person'):
                n = x['person']['name']
                k = nk(n.split(',')[1] + ' ' + n.split(',')[0]) if ',' in n else nk(n)
                out.setdefault(k, k.split())
    return out


def nadji(recenica, igraci):
    """Igrači tima pomenuti u rečenici: po prezimenu (poslednja reč ključa), uz ime kad dvojica imaju isto prezime."""
    r = ' ' + nk(recenica) + ' '
    prez = {}
    for k, reci in igraci.items():
        if reci:
            prez.setdefault(reci[-1], []).append(k)
    nadjeni = []
    for p, K in prez.items():
        if len(p) < 3 or f' {p} ' not in r:
            continue
        if len(K) == 1:
            nadjeni.append(K[0])
        else:
            nadjeni += [k for k in K if f' {k.split()[0]} ' in r]
    return nadjeni


def procitaj(url, igraci_po_timu, out, timovi):
    """Članak po utakmicama (zaglavlje „A vs. B (20:45 CET)“), pa po timovima; tekst tima se spaja u jedan pasus
    (ime igrača je često u posebnom redu), deli na rečenice i za svaku rečenicu se traže pomenuti igrači."""
    L = tekst_linije(get(url))
    par, tim_sad, pasus = None, None, []

    def zavrsi():
        if not tim_sad or not pasus:
            return
        x = ' '.join(pasus)
        if re.search(r'full roster', x, re.I):
            timovi.setdefault(tim_sad, {})['pun_sastav'] = True
        if re.search(r'not (yet )?(sent|submitted) an injury report', x, re.I):
            timovi.setdefault(tim_sad, {})['bez_izvestaja'] = True
        for rec in re.split(r'(?<=[a-z0-9\)”"])\.\s+(?=[A-Z“"])', x):
            st = stanje(rec)
            if not st:
                continue
            for k in nadji(rec, igraci_po_timu[tim_sad]):
                out[k] = dict(tim=tim_sad, stanje=st, tekst=rec[:300])

    for x in L:
        m = re.match(r'^(.+?) vs\.? (.+?) \(\d{1,2}:\d{2} CET\)$', x)
        if m:
            zavrsi()
            par, tim_sad, pasus = [tim(m.group(1)), tim(m.group(2))], None, []
            continue
        if not par:
            continue
        if re.match(r'^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), ', x) or re.match(r'^(Related|Read more|Tags)\b', x):
            zavrsi()
            par, tim_sad, pasus = None, None, []
            continue
        t = tim(x) if len(x.split()) <= 6 and not x.endswith('.') else None
        if t in par:
            zavrsi()
            tim_sad, pasus = t, []
            continue
        if tim_sad:
            pasus.append(x)
    zavrsi()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--kolo', type=int)
    a = ap.parse_args()
    sad = dt.datetime.now(dt.timezone.utc)
    U = utakmice()
    if a.kolo:
        kolo = a.kolo
    else:
        buduce = sorted([u for u in U if u['utc'] > sad - dt.timedelta(hours=3)], key=lambda u: u['utc'])
        kolo = buduce[0]['r'] if buduce else max(u['r'] for u in U)
    lista = get(LISTA)
    linkovi = sorted(set(re.findall(r'https://www\.eurohoops\.net/en/euroleague/(\d+)/([a-z0-9-]*injury-report[a-z0-9-]*)', lista)),
                     key=lambda x: int(x[0]))
    linkovi = [f'https://www.eurohoops.net/en/euroleague/{i}/{s}/' for i, s in linkovi if re.search(rf'round-{kolo}(?!\d)', s)]
    put = os.path.join(PROCENE, 'podaci', 'povrede.json')
    if not linkovi:
        print(f'povrede: za kolo {kolo} još nema izveštaja na Eurohoops')
        return
    kodovi = {u['dom'] for u in U if u['r'] == kolo} | {u['gost'] for u in U if u['r'] == kolo}
    igraci_po_timu = {k: igraci_tima(k) for k in kodovi}
    out, timovi = {}, {}
    for url in linkovi:                     # stariji pa noviji: noviji menja stanje
        procitaj(url, igraci_po_timu, out, timovi)
    for kod, x in timovi.items():          # „ceo sastav na raspolaganju“: niko iz tog tima nije van igre
        if x.get('pun_sastav'):
            for k, v in out.items():
                if v['tim'] == kod and v['stanje'] != 'igra':
                    v['stanje'] = 'igra'
    sacuvaj(put, dict(kolo=kolo, at=sad.astimezone(BG).strftime('%d.%m.%Y. %H:%M'), izvori=linkovi, igraci=out, timovi=timovi))
    from collections import Counter
    print(f"povrede: kolo {kolo}, članaka {len(linkovi)}, igrača {len(out)} ({dict(Counter(v['stanje'] for v in out.values()))})")


if __name__ == '__main__':
    main()
