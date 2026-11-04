"""Obrazloženja predloga ljudskim jezikom: zašto očekujemo to što očekujemo, bez procenata i računice.

Za igrača, stavku i granicu skuplja razloge iz statistike (procene/podaci/statistika.json), table (minuti, sastav,
odsutni), izveštaja o povredama i domaćih utakmica, i za svaki razlog zna na koju stranu gura (preko ili ispod).
  razlozi(...)  -> lista dict(p=važnost, d=+1 preko / -1 ispod, t=rečenica, kr=kratko, za zaključak)
  analiza(...)  -> rečenice u prilog strani (prva je zaključak: zašto je granica iznad ili ispod onoga što očekujemo),
                   a sa protiv>0 i rečenice koje govore protiv
Koriste ga predlozi.py (kartice predloga i kartica Igrači).
"""
import datetime as dt, math, os, re
from zajedno import PROCENE, ucitaj, nk

IME = {'MAD': 'Real', 'BAR': 'Barselona', 'BAS': 'Baskonija', 'BES': 'Bešiktaš', 'DUB': 'Dubai', 'HTA': 'Hapoel', 'IST': 'Efes',
       'MIL': 'Milano', 'MUN': 'Bajern', 'OLY': 'Olimpijakos', 'PAM': 'Valensija', 'PAN': 'Panatinaikos', 'PAR': 'Partizan',
       'PRS': 'Pariz', 'RED': 'Zvezda', 'TEL': 'Makabi', 'ULK': 'Fenerbahče', 'VIR': 'Virtus', 'ZAL': 'Žalgiris', 'ASV': 'Asvel'}
GEN = {'MAD': 'Reala', 'BAR': 'Barselone', 'BAS': 'Baskonije', 'BES': 'Bešiktaša', 'DUB': 'Dubaija', 'HTA': 'Hapoela', 'IST': 'Efesa',
       'MIL': 'Milana', 'MUN': 'Bajerna', 'OLY': 'Olimpijakosa', 'PAM': 'Valensije', 'PAN': 'Panatinaikosa', 'PAR': 'Partizana',
       'PRS': 'Pariza', 'RED': 'Zvezde', 'TEL': 'Makabija', 'ULK': 'Fenerbahčea', 'VIR': 'Virtusa', 'ZAL': 'Žalgirisa', 'ASV': 'Asvela'}
POZ_NOM = {'G': 'bekovi', 'F': 'krila', 'C': 'centri'}
POZ_AK = {'G': 'bekove', 'F': 'krila', 'C': 'centre'}
POZ_JED = {'G': 'bek', 'F': 'krilo', 'C': 'centar'}
BROJ = ['nula', 'jedan', 'dva', 'tri', 'četiri', 'pet', 'šest', 'sedam', 'osam', 'devet', 'deset']


def ime(kod):
    return IME.get(kod, kod)


def gen(kod):
    return GEN.get(kod, kod)


def broj(n, s=None):
    """Broj rečima do deset (ženski rod za asistencije: jedna, dve), veći ciframa."""
    n = int(n)
    if s == 'A' and n in (1, 2):
        return 'jedna' if n == 1 else 'dve'
    return BROJ[n] if 0 <= n <= 10 else str(n)


def imenica(n, s):
    """Oblik imenice uz broj: poen, skok, asistencija, minut."""
    n = int(n)
    d, s100 = n % 10, n % 100
    jed = d == 1 and s100 != 11
    mal = 2 <= d <= 4 and not 12 <= s100 <= 14
    if s == 'P':
        return 'poen' if jed else 'poena'
    if s == 'S':
        return 'skok' if jed else 'skoka' if mal else 'skokova'
    if s == 'A':
        return 'asistencija' if jed else 'asistencije' if mal else 'asistencija'
    if s == 'min':
        return 'minut' if jed else 'minuta'
    return ''


GEN1 = {'P': 'jednog poena', 'S': 'jednog skoka', 'A': 'jedne asistencije', 'min': 'jednog minuta'}


def oko(x, s):
    """„oko tri skoka“, „tri do četiri skoka“, „oko 13 poena“, „oko jednog skoka“."""
    r = round(x * 2) / 2
    if r == int(r):
        if int(r) == 0:
            return 'skoro ništa'
        if int(r) == 1:
            return 'oko ' + GEN1.get(s, 'jednog')
        return f'oko {broj(r, s)} {imenica(r, s)}'
    a, b = int(math.floor(r)), int(math.ceil(r))
    if b > 10:
        return f'{a} do {b} {imenica(b, s)}'
    return f'{broj(a, s)} do {broj(b, s)} {imenica(b, s)}'


def utak(n):
    """„od 9 utakmica“, „od 3 utakmice“."""
    n = int(n)
    d, s100 = n % 10, n % 100
    return 'utakmice' if (d == 1 and s100 != 11) or (2 <= d <= 4 and not 12 <= s100 <= 14) else 'utakmica'


def zr(x):
    return f'{x:g}'.replace('.', ',')


def prezime(puno):
    w = [x for x in str(puno).split() if x.rstrip('.') not in ('Jr', 'Sr', 'II', 'III', 'IV')]
    return w[-1] if w else puno


def spisak(L):
    L = list(L)
    return L[0] if len(L) == 1 else ', '.join(L[:-1]) + ' i ' + L[-1]


class Kontekst:
    """Sve što obrazloženja čitaju, učitano jednom."""

    def __init__(self, B, domacin):
        self.B, self.domacin = B, domacin
        p = os.path.join(PROCENE, 'podaci', 'statistika.json')
        self.ST = ucitaj(p) if os.path.exists(p) else {'timovi': {}, 'igraci': {}, 'liga': {}}
        p = os.path.join(PROCENE, 'podaci', 'domace', 'utakmice.json')
        self.dom = list(ucitaj(p).values()) if os.path.exists(p) else []

    def domace_pre(self, kod, k, dan, dana=3):
        """Domaće utakmice tima u `dana` dana pre dana utakmice i minuti igrača u njima: [(dana pre, minuti)]."""
        d0 = dt.date.fromisoformat(dan)
        kljuc = k.split()
        out = []
        for u in self.dom:
            if u['kod'] != kod or not u.get('igraci'):
                continue
            du = dt.datetime.fromtimestamp(u['t'], dt.timezone.utc).date()
            razlika = (d0 - du).days
            if not 1 <= razlika <= dana:
                continue
            sk = u['skr'][0] if u['kuca'] else u['skr'][1]
            for ime_fs, m, *_ in u['igraci'].get(sk, []):
                t = [x for x in nk(ime_fs).split() if len(x) > 1]
                if t and kljuc[-len(t):] == t:
                    out.append((razlika, m))
        return out


def razlozi(i, s, l, u, moja, tudja, K):
    """Svi razlozi za igrača i (iz table), stavku s, granicu l. moja/tudja: strana iz table (tim, igraci, nedostaju)."""
    B, ST = K.B, K.ST
    x = i['s'][s]
    g = [r for r in B.byk.get(i['k'], []) if r['dan'] < u['dan']]
    T = []
    sg = lambda v: (v > 0) - (v < 0)
    tim, prot = moja['tim'], moja['prot']
    van = {j['k'] for j in moja.get('nedostaju', [])} | {j['k'] for j in moja['igraci'] if j['ne_igra']}
    sti = ST['igraci'].get(i['k'], {})
    poz = i['pos']
    # 1) sezona naspram granice
    if g:
        n = len(g)
        pros = sum(r[s] for r in g) / n
        n_o, n_u = sum(r[s] > l for r in g), sum(r[s] < l for r in g)
        d = sg(n_o - n_u) or sg(pros - l)
        if d > 0:
            T.append(dict(p=2, d=1, t=f"Ove sezone daje {oko(pros, s)} po utakmici i granicu od {zr(l)} prebacio je u {n_o} od {n} {utak(n)}.",
                          kr='redovno prebacuje ovu granicu' if n_o * 3 >= n * 2 else 'češće je preko nego ispod ove granice'))
        elif d < 0:
            T.append(dict(p=2, d=-1, t=f"Ove sezone daje {oko(pros, s)} po utakmici; ispod {zr(l)} je ostao u {n_u} od {n} {utak(n)}.",
                          kr='u većini utakmica ostaje ispod ove granice' if n_u * 3 >= n * 2 else 'češće ostaje ispod nego preko ove granice'))
        # forma
        if n >= 4:
            l3 = [r[s] for r in g[-3:]]
            a3 = sum(l3) / 3
            if abs(a3 - pros) >= max(1.0, 0.15 * pros):
                vise = a3 > pros
                T.append(dict(p=5, d=1 if vise else -1,
                              t=f"U poslednje tri utakmice: {spisak([str(v) for v in l3])} {imenica(l3[-1], s)}, {'više' if vise else 'manje'} nego inače.",
                              kr=f"u poslednjim utakmicama daje {'više' if vise else 'manje'} nego inače"))
        # dom i gost
        je_kuca = u['dom'] == tim
        kuca = [r[s] for r in g if K.domacin.get(r['g']) == r['team']]
        gost = [r[s] for r in g if K.domacin.get(r['g']) and K.domacin.get(r['g']) != r['team']]
        if len(kuca) >= 2 and len(gost) >= 2:
            ak, ag = sum(kuca) / len(kuca), sum(gost) / len(gost)
            ova, druga = (ak, ag) if je_kuca else (ag, ak)
            if abs(ak - ag) >= max(1.0, 0.2 * max(ak, ag)):
                gde, gde2 = ('Kod kuće', 'u gostima') if je_kuca else ('U gostima', 'kod kuće')
                gl = {'P': 'postiže', 'S': 'hvata', 'A': 'deli'}[s]
                im = {'P': 'poena', 'S': 'skokova', 'A': 'asistencija'}[s]
                vise = ova > druga
                T.append(dict(p=9, d=sg(ova - druga), t=f"{gde} {gl} {'više' if vise else 'manje'} {im} nego {gde2} ({oko(ova, s)} naspram {oko(druga, s)}), a sada igra {gde.lower()}.",
                              kr=f"{gde.lower()} {gl} {'više' if vise else 'manje'}"))
        isti = [r for r in g if r['opp'] == prot]
        if isti and (all(r[s] > l for r in isti) or all(r[s] < l for r in isti)):
            T.append(dict(p=7, d=1 if isti[0][s] > l else -1,
                          t=f"Protiv {gen(prot)} je ove sezone imao {spisak([str(r[s]) for r in isti[-2:]])} {imenica(isti[-1][s], s)}.", kr=''))
    # 2) uloga u timu
    drug = [ST['igraci'][j['k']] for j in moja['igraci'] if j['k'] in ST['igraci'] and j['k'] != i['k'] and j['k'] not in van
            and ST['igraci'][j['k']]['n'] >= 3]
    if sti and sti.get('n', 0) >= 3:
        if s == 'S':
            sk = sorted(drug, key=lambda y: -y['S'])[:2]
            if poz == 'G' and sti.get('mS', 9) >= 3 and sk:
                T.append(dict(p=3, d=-1, t=f"Kao bek retko ide u skok; odbijene lopte kod {gen(tim)} uglavnom hvataju {spisak([prezime(y['ime']) for y in sk])}.",
                              kr='kao bek retko ide u skok'))
            elif sti.get('mS') == 1 or (sk and sti['S'] >= sk[0]['S']):
                T.append(dict(p=3, d=1, t=f"Glavni je skakač {gen(tim)}: niko u timu ne hvata više odbijenih lopti.", kr='glavni je skakač tima'))
            elif poz in ('F', 'C') and sk and sk[0]['S'] > sti['S'] + 1.5:
                T.append(dict(p=4, d=-1, t=f"Glavni skakač {gen(tim)} je {prezime(sk[0]['ime'])}, pa za njega ostaje manje odbijenih lopti.",
                              kr=f"glavni skakač tima je {prezime(sk[0]['ime'])}"))
        elif s == 'A':
            org = sorted(drug, key=lambda y: -y['A'])[:2]
            if sti.get('mA') == 1 or (org and sti['A'] >= org[0]['A']):
                T.append(dict(p=3, d=1, t=f"Prvi je organizator igre {gen(tim)}: lopta je najčešće u njegovim rukama.", kr='prvi je organizator igre'))
            elif org and org[0]['A'] > sti['A'] + 1:
                T.append(dict(p=3, d=-1, t=f"Nije glavni organizator; loptu kod {gen(tim)} uglavnom vode {spisak([prezime(y['ime']) for y in org])}.",
                              kr='nije glavni organizator igre'))
        elif s == 'P':
            st = sorted(drug, key=lambda y: -y['P'])[:2]
            if sti.get('mP', 9) <= 2 or (st and sti['P'] >= st[0]['P']):
                T.append(dict(p=3, d=1, t=f"Jedna je od prvih opcija u napadu {gen(tim)}.", kr='jedna je od prvih opcija u napadu'))
            elif len(st) == 2 and st[1]['P'] > sti['P'] + 2:
                T.append(dict(p=3, d=-1, t=f"Nije među prvim opcijama u napadu; više šuteva dobijaju {spisak([prezime(y['ime']) for y in st])}.",
                              kr='nije među prvim opcijama u napadu'))
        # minuti i uloga
        if sti['st'] / sti['n'] < 0.4 and i['min'] < 22:
            T.append(dict(p=4, d=-1, t=f"Dolazi sa klupe i igra {oko(i['min'], 'min')}.", kr='dolazi sa klupe'))
        elif i['min'] >= 28:
            T.append(dict(p=4, d=1, t=f"Igra velike minute, {oko(i['min'], 'min')} po utakmici.", kr='igra velike minute'))
    pm = i.get('posl_min') or []
    if len(pm) >= 3:
        m3 = sum(pm[-3:]) / 3
        if abs(m3 - i['min']) >= 3:
            vise = m3 > i['min']
            T.append(dict(p=4, d=1 if vise else -1, t=f"U poslednjim utakmicama igra {'više' if vise else 'manje'} nego ranije ({spisak([str(m) for m in pm[-3:]])} minuta).",
                          kr=f"u poslednje vreme igra {'više' if vise else 'manje'}"))
    if i.get('min_cv', 0) >= 0.35:
        T.append(dict(p=8, d=-1, t='Minutaža mu dosta varira od utakmice do utakmice, pa je teško računati na veliki učinak.', kr='minutaža mu varira'))
    # 3) protivnik
    tp = ST['timovi'].get(prot, {})
    tz = tp.get('poz', {}).get(poz, {})
    if s == 'P' and tp:
        ip, dr = tz.get('iP', 1), tp.get('mesto', {}).get('drtg', 10)
        if ip <= 0.92 or (dr >= 16 and ip <= 1.0):
            T.append(dict(p=3, d=-1, t=f"{ime(prot)} dobro brani {POZ_AK.get(poz, 'ovu poziciju')}" + ('; to je i jedna od najboljih odbrana u ligi.' if dr >= 16 else '.'),
                          kr=f"{ime(prot)} dobro brani {POZ_AK.get(poz, 'ovu poziciju')}"))
        elif ip >= 1.08 or (dr <= 5 and ip >= 1.0):
            T.append(dict(p=3, d=1, t=f"Protiv {gen(prot)} {POZ_NOM.get(poz, 'igrači na ovoj poziciji')} postižu više nego protiv većine ekipa" + ('; odbrana im je među slabijim u ligi.' if dr <= 5 else '.'),
                          kr=f"protiv {gen(prot)} {POZ_NOM.get(poz, 'igrači na ovoj poziciji')} postižu više"))
    if s == 'S' and tp:
        m_dr, m_osk = tp.get('mesto', {}).get('dr_pct', 10), tp.get('mesto', {}).get('o_sk', 10)
        if m_dr <= 5 or m_osk >= 16:
            T.append(dict(p=5, d=-1, t=f"{ime(prot)} dobro zatvara skok: protiv njih se hvata malo odbijenih lopti.", kr=f"{ime(prot)} dobro zatvara skok"))
        elif m_dr >= 16 or m_osk <= 5:
            T.append(dict(p=5, d=1, t=f"Protiv {gen(prot)} se skače: dozvoljavaju dosta odbijenih lopti.", kr=f"protiv {gen(prot)} se skače"))
    if s == 'A' and tp:
        m_oa, ia = tp.get('mesto', {}).get('o_ast', 10), tz.get('iA', 1)
        if m_oa >= 16 or ia <= 0.9:
            T.append(dict(p=4, d=-1, t=f"{ime(prot)} ne dozvoljava laku igru dodavanjem; protiv njih se deli malo asistencija.", kr=f"{ime(prot)} ne dozvoljava mnogo asistencija"))
        elif m_oa <= 5 or ia >= 1.1:
            T.append(dict(p=4, d=1, t=f"Protiv {gen(prot)} lopta dobro kruži; dozvoljavaju dosta asistencija.", kr=f"protiv {gen(prot)} se lako dodaje"))
    # 4) tempo
    if s in ('P', 'A'):
        t1, t2 = ST['timovi'].get(tim, {}).get('mesto', {}).get('tempo'), tp.get('mesto', {}).get('tempo')
        if t1 and t2:
            sr = (t1 + t2) / 2
            if sr <= 6:
                T.append(dict(p=7, d=1, t='Obe ekipe vole brz ritam, pa će biti više napada nego obično.', kr='utakmica obećava brz ritam'))
            elif sr >= 15:
                T.append(dict(p=7, d=-1, t='Obe ekipe igraju sporo, pa će napada biti manje nego obično.', kr='obe ekipe igraju sporo'))
    # 5) saigrači: odsutni i povratak
    ned = [j for j in moja.get('nedostaju', []) if j['k'] != i['k']]
    if ned:
        T.append(dict(p=1, d=1, t=f"Kod {gen(tim)} ne {'igraju' if len(ned) > 1 else 'igra'} {spisak([j['ime'] for j in ned[:3]])}, pa ostaje više minuta i lopti za ostale.",
                      kr=f"bez {'njih' if len(ned) > 1 else 'njega'} ostaje više prostora"))
    ned2 = [j for j in tudja.get('nedostaju', []) if j['pos'] == poz]
    if ned2:
        T.append(dict(p=6, d=1, t=f"Kod {gen(prot)} na njegovoj poziciji ne {'igraju' if len(ned2) > 1 else 'igra'} {spisak([j['ime'] for j in ned2[:2]])}.", kr=''))
    vraca = [j for j in moja['igraci'] if j['k'] != i['k'] and j.get('izvestaj') == 'igra' and j['odsutan'] >= 1 and j['pos'] == poz and j['min'] >= 12]
    if vraca:
        T.append(dict(p=3, d=-1, t=f"Na raspolaganju je ponovo i {spisak([j['ime'] for j in vraca[:2]])}, pa minuti na njegovoj poziciji mogu da budu podeljeni.",
                      kr='minuti na njegovoj poziciji mogu da budu podeljeni'))
    # 6) raspored: domaća utakmica pre dva-tri dana sa velikom minutažom
    dp = K.domace_pre(tim, i['k'], u['dan'], dana=2)
    if dp:
        dana, m = min(dp)
        if m >= 28:
            T.append(dict(p=8, d=-1, t=f"{'Juče' if dana == 1 else 'Prekjuče'} je u prvenstvu igrao {broj(round(m))} {imenica(round(m), 'min')}, pa u ovu utakmicu ulazi bez pravog odmora.",
                          kr='u utakmicu ulazi bez pravog odmora'))
    # zaključak: granica naspram očekivanja
    mu = x['mu']
    raz = mu - l
    if abs(raz) >= 0.3:
        d = 1 if raz > 0 else -1
        T.append(dict(p=0, d=d, t=f"Granica od {zr(l)} je {'niža' if d > 0 else 'viša'} od onoga što realno očekujemo, a to je {oko(mu, s)}.", kr='', zak=True))
    return T


def analiza(i, s, pr, u, moja, tudja, K, najvise=6, protiv=0):
    """Rečenice u prilog strani pr['strana'] na granici pr['l'] (najviše `najvise`, prva je zaključak ako ga ima);
    sa protiv>0 vraća (za, protiv) sa do `protiv` rečenica koje govore protiv."""
    smer = 1 if pr['strana'] == 'o' else -1
    T = sorted(razlozi(i, s, pr['l'], u, moja, tudja, K), key=lambda y: y['p'])
    Z = [y for y in T if y['d'] == smer]
    ostali = [y for y in Z if not y.get('zak')]
    for y in Z:
        if y.get('zak'):
            # zaključak: kad nema drugih razloga, razlog ide u istu rečenicu; inače su razlozi u tačkama ispod
            kr = [z['kr'] for z in ostali if z['kr']][:2]
            if len(ostali) <= 1 and kr:
                y['t'] = y['t'][:-1] + ': ' + ', a '.join(kr) + '.'
                ostali = []
            elif ostali:
                y['t'] = y['t'][:-1] + ', iz ovih razloga:'
    za = [y['t'] for y in Z if y.get('zak')] + [y['t'] for y in ostali]
    za = za[:najvise]
    if not protiv:
        return za
    return za, [y['t'] for y in T if y['d'] == -smer][:protiv]
