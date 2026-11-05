"""Izveštaj o povredama za tekuće kolo: zvanični izveštaj Evrolige preko Eurohoops prenosa (zvanični portal odbija automatski
pristup) i dnevni izveštaj BasketNews-a (https://basketnews.com/leagues/25-euroleague/injured.html), koji ima prednost.

  python3 procene/skripte/povrede.py            tekuće kolo
  python3 procene/skripte/povrede.py --kolo 10

Eurohoops za svako kolo objavi izveštaj (i dopune pred drugi dan kola). Skripta nađe te članke na
https://www.eurohoops.net/en/euroleague/ (naslov sadrži „injury report“ i „round N“), pročita ih po utakmicama i timovima
i za svakog pomenutog igrača odredi stanje iz rečenice:
  van     van igre (povreda, „out“, „ruled out“, ili „last played“ i sl. uz povredu)
  upitan  neizvestan („questionable“, „game-time decision“, „doubtful“ ...), i samo „last played“, „yet to play“,
          „has not featured“ bez pomena povrede, ili kad piše da igra u domaćem prvenstvu
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
R_POVREDA = re.compile(r'\b(out|ruled out|will miss|misses|miss|sidelined|injur\w*|sprain\w*|ruptur\w*|tear|torn|surgery|fractur\w*|strain\w*|'
                       r'suspend\w*|concussion|illness|sick|knee|ankle|hamstring|calf|shoulder|foot|back pain|achilles)\b', re.I)
# samo opis da igrač nije igrao (bez povrede): nije potvrda da je van igre (4.11.: Llull, Smith i Sarr su igrali)
R_ODSUSTVO = re.compile(r'\b(last played|has not featured|hasn.t featured|has not played|yet to play|not on the (\w+ ){0,3}roster|'
                        r'did not make the (\w+ )?roster|missed|did not play|did not feature|absentee)\b', re.I)
R_POTVRDA = re.compile(r'\b(confirmed .{0,40}absentee|confirmed .{0,30}(will|is set to) miss|will not play|ruled out for (this|tonight|thursday|friday|wednesday|tuesday))', re.I)
R_IPAK = re.compile(r'\b(although he has been play\w*|but has (featured|played)|has been playing|has featured in the \w+ league|played in the \w+ league)\b', re.I)


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


def tim_iz(naziv):
    """Tim iz punog naziva sa sponzorom („Hapoel IBI Tel Aviv“): ceo naziv, pa kraći delovi."""
    r = tim(naziv)
    if r:
        return r
    w = naziv.split()
    for n in range(len(w) - 1, 0, -1):
        for i in range(0, len(w) - n + 1):
            r = tim(' '.join(w[i:i + n]))
            if r:
                return r
    return None


def stanje(recenica):
    if R_NIJE.search(recenica) or R_POTVRDA.search(recenica):
        return 'van'
    if R_IGRA.search(recenica):
        return 'igra'
    if R_UPITAN.search(recenica) or R_IPAK.search(recenica):
        return 'upitan'
    if R_ODSUSTVO.search(recenica) and not R_POVREDA.search(recenica):
        return 'upitan'
    if R_POVREDA.search(recenica) or R_ODSUSTVO.search(recenica):
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


def procitaj(url, igraci_po_timu, out, timovi, novi):
    """Članak po utakmicama (zaglavlje „A vs. B (20:45 CET)“), pa po timovima; tekst tima se spaja u jedan pasus
    (ime igrača je često u posebnom redu), deli na rečenice i za svaku rečenicu se traže pomenuti igrači."""
    L = tekst_linije(get(url))
    par, tim_sad, pasus = None, None, []

    def zavrsi():
        if not tim_sad or not pasus:
            return
        x = ' '.join(pasus)
        # „ceo sastav“ samo kad se odnosi na ovu utakmicu (ne „had his full roster available ahead of Round 9“)
        if re.search(r'full roster', x, re.I) and not re.search(r'full roster available (in|ahead of|for) round', x, re.I):
            timovi.setdefault(tim_sad, {})['pun_sastav'] = True
        if re.search(r'not (yet )?(sent|submitted) an injury report', x, re.I):
            timovi.setdefault(tim_sad, {})['bez_izvestaja'] = True
        for m in re.finditer(r'[Nn]ew signing ([A-Z][\w\'’-]+(?: [A-Z][\w\'’-]+)+) has been registered', x):
            novi[nk(m.group(1))] = dict(tim=tim_sad, ime=m.group(1), tekst=m.group(0)[:200])
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
            par, tim_sad, pasus = [tim_iz(m.group(1)), tim_iz(m.group(2))], None, []
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


BN_URL = 'https://basketnews.com/leagues/25-euroleague/injured.html'
BN_STANJE = {'Out': 'van', 'Doubtful': 'upitan', 'Uncertain': 'upitan', 'Game-time': 'upitan', 'Questionable': 'upitan',
             'Expected': 'igra', 'Ready': 'igra', 'Probable': 'igra', 'Available': 'igra'}
R_BN = re.compile(r"\b(PG|SG|SF|PF|C|G|F)\s+((?:[A-Z][\w'’.-]*\s?){1,4}?)\s+(Out|Doubtful|Uncertain|Game-time|Expected|Ready|Questionable|Probable|Available)"
                  r"\s+(?:Round\s+(\d+)|(Out for season|Out indefinitely))\s+(.*?)(?=\s(?:PG|SG|SF|PF|C|G|F)\s+[A-Z][\w'’.-]*\s+[A-Z]|$)")


def basketnews(kolo, igraci_po_timu):
    """BasketNews dnevni izveštaj o povredama Evrolige: igrač -> stanje za ovo kolo (Out = van, Doubtful/Uncertain/Game-time = upitan,
    Expected/Ready = igra). Igrač se prepoznaje po imenu među igračima timova iz kola."""
    L = ' '.join(tekst_linije(get(BN_URL)))
    i = L.find('P Player Status Round Comments')
    if i < 0:
        print('basketnews: izveštaj nije pročitan')
        return {}
    out = {}
    sve = {}
    B = getattr(igraci_tima, 'B', None)
    for kod, ig in igraci_po_timu.items():
        for k, reci in ig.items():
            zadnji = B.byk[k][-1]['team'] if B is not None and B.byk.get(k) else None
            if k not in sve or zadnji == kod:          # igrač sa spiska više klubova: tim za koji je poslednji igrao
                sve[k] = (kod, reci)
    for poz, ime, st, rnd, sezona, kom in R_BN.findall(L[i:]):
        if rnd and int(rnd) != kolo:
            continue
        n = nk(ime).replace('.', ' ').split()
        if not n:
            continue
        kand = [k for k, (kod, reci) in sve.items() if reci and reci[-1] == n[-1] and (len(n) == 1 or reci[0][0] == n[0][0])]
        if len(kand) != 1:
            continue
        k = kand[0]
        out[k] = dict(tim=sve[k][0], stanje=BN_STANJE[st], tekst=f'{st}: {kom}'[:300], izvor='basketnews')
    return out


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
    out, timovi, novi = {}, {}, {}
    for url in linkovi:                     # stariji pa noviji: noviji menja stanje
        procitaj(url, igraci_po_timu, out, timovi, novi)
    # BasketNews (ažurira se svakog dana, po kolu): ima prednost nad Eurohoops prenosom
    bn = basketnews(kolo, igraci_po_timu)
    for k, v in bn.items():
        if k in out:
            v['tekst'] = v['tekst'] + ' | Eurohoops: ' + out[k]['tekst'][:150]
        out[k] = v
    print(f'basketnews: igrača {len(bn)}')
    for kod, x in timovi.items():          # „ceo sastav na raspolaganju“: niko iz tog tima nije van igre
        if x.get('pun_sastav'):
            for k, v in out.items():
                if v['tim'] == kod and v['stanje'] != 'igra':
                    v['stanje'] = 'igra'
    # pozicija novih igrača sa zvaničnog spiska kluba (Evroliga API)
    POZ = {'Guard': 'G', 'Forward': 'F', 'Center': 'C'}
    for k, v in novi.items():
        try:
            req = urllib.request.Request(f"https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/clubs/{v['tim']}/people", headers={'User-Agent': 'curl/8.5.0'})
            for x in json.loads(urllib.request.urlopen(req, timeout=20).read()):
                n = x.get('person', {}).get('name', '')
                if x.get('type') == 'J' and ',' in n and nk(n.split(',')[1] + ' ' + n.split(',')[0]) == k:
                    v['pos'] = POZ.get(x.get('positionName') or '', '')
        except Exception as e:
            print('pozicija novog igrača:', k, e)
    sacuvaj(put, dict(kolo=kolo, at=sad.astimezone(BG).strftime('%d.%m.%Y. %H:%M'), izvori=linkovi, igraci=out, timovi=timovi, novi=novi))
    from collections import Counter
    print(f"povrede: kolo {kolo}, članaka {len(linkovi)}, igrača {len(out)} ({dict(Counter(v['stanje'] for v in out.values()))})")


if __name__ == '__main__':
    main()
