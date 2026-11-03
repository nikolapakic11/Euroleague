"""Zajedničke funkcije za projekat procene.

Čita samo iz baza/. Ništa iz minusi/.
"""
import json, os, re, unicodedata, datetime as dt
from zoneinfo import ZoneInfo

KOREN = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
BAZA = os.path.join(KOREN, 'baza')
PROCENE = os.path.join(KOREN, 'procene')
BG = ZoneInfo('Europe/Belgrade')

SUF = {'jr', 'sr', 'ii', 'iii', 'iv'}


def nk(x):
    """Ključ imena igrača (isti postupak kao baza/skripte/build.py)."""
    t = unicodedata.normalize('NFD', str(x or ''))
    t = ''.join(ch for ch in t if unicodedata.category(ch) != 'Mn').lower().replace('đ', 'dj')
    t = re.sub(r'\b([a-z])\.\s*([a-z])\.', r'\1\2', t)
    t = re.sub(r"[-.']", ' ', t)
    t = re.sub(r'[^a-z ]', '', t)
    return ' '.join(w for w in t.split() if w not in SUF)


def pn(n):
    """Ime iz zapisnika ('PREZIME, IME') u ključ."""
    if ',' in n:
        a = n.split(',')
        return nk(a[1] + ' ' + a[0])
    return nk(n)


# Nazivi timova kod kladionica -> kod Evrolige
TIM = {
    'anadolu efes': 'IST', 'efes': 'IST', 'anadolu efes istanbul': 'IST',
    'barcelona': 'BAR', 'fc barcelona': 'BAR',
    'baskonia': 'BAS', 'kosner baskonia': 'BAS',
    'bayern': 'MUN', 'bayern munich': 'MUN', 'bayern munchen': 'MUN', 'fc bayern munich': 'MUN',
    'besiktas': 'BES',
    'crvena zvezda': 'RED', 'zvezda': 'RED', 'crvena zvezda meridianbet': 'RED',
    'dubai': 'DUB', 'dubai basketball': 'DUB',
    'fenerbahce': 'ULK',
    'hapoel tel aviv': 'HTA', 'hapoel tel-aviv': 'HTA', 'hapoel ta': 'HTA', 'hapoel t a': 'HTA',
    'lyon villeurbanne': 'ASV', 'asvel': 'ASV', 'lyon-villeurbanne': 'ASV', 'villeurbanne': 'ASV',
    'maccabi tel aviv': 'TEL', 'maccabi t a': 'TEL', 'maccabi ta': 'TEL', 'maccabi': 'TEL',
    'olimpia milano': 'MIL', 'milano': 'MIL', 'olimpia milan': 'MIL', 'armani milano': 'MIL',
    'olympiacos': 'OLY', 'olympiakos': 'OLY', 'olimpijakos': 'OLY',
    'panathinaikos': 'PAN', 'panatinaikos': 'PAN',
    'paris': 'PRS', 'paris basketball': 'PRS',
    'partizan': 'PAR',
    'real madrid': 'MAD', 'real': 'MAD',
    'valencia': 'PAM', 'valencia basket': 'PAM',
    'virtus bologna': 'VIR', 'virtus': 'VIR',
    'zalgiris': 'ZAL', 'zalgiris kaunas': 'ZAL',
}


def tim(naziv):
    k = nk(naziv)
    if k in TIM:
        return TIM[k]
    k2 = re.sub(r'\s+', ' ', str(naziv or '').lower().strip())
    if k2 in TIM:
        return TIM[k2]
    for a, c in TIM.items():
        if len(a) > 4 and (a in k or k in a):
            return c
    return None


def ucitaj(putanja):
    with open(putanja, encoding='utf-8') as f:
        return json.load(f)


def sacuvaj(putanja, podaci, kompaktno=False):
    os.makedirs(os.path.dirname(putanja), exist_ok=True)
    with open(putanja, 'w', encoding='utf-8') as f:
        if kompaktno:
            json.dump(podaci, f, ensure_ascii=False, separators=(',', ':'))
        else:
            json.dump(podaci, f, ensure_ascii=False, indent=1)


def utakmice():
    """Raspored: lista dict(g, r, utc, dan (lokalni datum), dom, gost)."""
    out = []
    for x in ucitaj(os.path.join(BAZA, 'games.json'))['data']:
        u = dt.datetime.fromisoformat(x['utcDate'].replace('Z', '+00:00'))
        out.append(dict(g=x['gameCode'], r=x['round'], utc=u, dan=u.astimezone(BG).date().isoformat(),
                        dom=x['local']['club']['code'], gost=x['road']['club']['code'], odigrana=x['played']))
    return out


def nadji_utakmicu(kod_tima, utc, lista=None):
    """Utakmica tima najbliža datom trenutku (do 18 sati razlike)."""
    lista = lista or utakmice()
    best = None
    for u in lista:
        if kod_tima in (u['dom'], u['gost']):
            d = abs((u['utc'] - utc).total_seconds())
            if d < 18 * 3600 and (best is None or d < best[0]):
                best = (d, u)
    return best[1] if best else None


def sledece_slovo(folder, dan):
    """Sledeći slobodan snimak za dan: a, b, c..."""
    os.makedirs(folder, exist_ok=True)
    for s in 'abcdefghijklmnopqrstuvwxyz':
        if not os.path.exists(os.path.join(folder, f'{dan}_{s}.json')):
            return s
    raise RuntimeError('previše snimaka za ' + dan)
