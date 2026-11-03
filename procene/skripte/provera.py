"""Provera modela raspona na ponudama od oktobra, u oba smera (preko i ispod).

  python3 procene/skripte/provera.py

Ponude (samo podaci o granicama i kvotama, iz baza/):
  - baza/ds_all.json: Admiral, 8.10. do 23.10. (koriste se samo dan, igrač, stavka, granica, kvote)
  - baza/ponude/admiral/*.json: poslednji snimak dana, od 27.10.
  - baza/ponude/maxbet/*.json
  - baza/ponude/soccerbet/*.json i baza/ponude/mozzart/*.json kad ih bude
Za svaku granicu model računa verovatnoću iz utakmica pre tog dana i poredi je sa ishodom
i sa verovatnoćom koju daju kvote (bez marže). Igrač koji nije igrao: granica se ne računa.

Izlaz: procene/provera/izvestaj.md i procene/provera/granice.json
"""
import collections, glob, json, math, os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import model
from model import Baza, verovatnoca_preko, percentili
from zajedno import kljuc_snimka, BAZA, PROCENE, ucitaj, sacuvaj, tim

MESECI = re.compile(r'(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})')


def dan_iz_vremena(t, rezerva):
    m = MESECI.search(t or '')
    if m:
        return f'{m.group(3)}-{int(m.group(2)):02d}-{int(m.group(1)):02d}'
    m = re.match(r'(\d{4}-\d{2}-\d{2})', t or '')
    return m.group(1) if m else rezerva


def ponude():
    out = []
    # Admiral 8.10.-23.10. iz ds_all (samo podaci ponude)
    for x in ucitaj(os.path.join(BAZA, 'ds_all.json')):
        f = x['fair']
        o = x['u'] * f / (1 - f) if 0 < f < 1 else None
        if not o:
            continue
        out.append(dict(izvor='admiral', dan=x['day'], p=x['p'], tk=x['team'], s=x['s'], l=x['l'], u=x['u'], o=round(o, 3)))
    # snimci po kladionicama: poslednji snimak dana
    for kl in ('admiral', 'maxbet', 'soccerbet', 'mozzart'):
        po_danu = collections.defaultdict(list)
        for f in sorted(glob.glob(os.path.join(BAZA, 'ponude', kl, '*.json')), key=kljuc_snimka):
            ime = os.path.basename(f)
            md = re.search(r'\d{4}-\d{2}-\d{2}', ime)
            if not md:
                continue
            ime = ime[md.start():]
            j = ucitaj(f)
            if 'picks' not in j:
                continue
            po_danu[ime[:10]].append(j)
        for d, snimci in po_danu.items():
            j = snimci[-1]
            for p in j['picks']:
                if p.get('s') not in ('P', 'S', 'A') or not p.get('u') or not p.get('o'):
                    continue
                if 'm' in p and not p['m'] and kl != 'soccerbet':
                    continue
                out.append(dict(izvor=kl, dan=dan_iz_vremena(p.get('time'), d), p=p['p'], tk=p.get('tk') or (None if ' | ' in (p.get('t') or '') else tim(p.get('t'))), t=p.get('t'),
                                s=p['s'], l=p['l'], u=p['u'], o=p['o'], glavna=p.get('m', 1)))
    # duplikati (isti izvor, dan, igrač, stavka, granica)
    vid, cist = set(), []
    for x in out:
        kl = (x['izvor'], x['dan'], x['p'].lower(), x['s'], x['l'])
        if kl not in vid:
            vid.add(kl); cist.append(x)
    return cist


def ll(p, y):
    p = min(max(p, 1e-4), 1 - 1e-4)
    return -(y * math.log(p) + (1 - y) * math.log(1 - p))


def main():
    model.ucitaj_parametre()
    B = Baza()
    kolo_dana = {r['dan']: r['r'] for r in B.rows}
    rez, nema_igraca, nije_igrao = [], collections.Counter(), 0
    for x in ponude():
        k, _ = B.nadji_u_utakmici(x['p'], x.get('t'), x['tk'])
        if not k:
            nema_igraca[x['p']] += 1
            continue
        danas = [r for r in B.byk[k] if r['dan'] == x['dan']]
        if not danas:
            nije_igrao += 1
            continue
        r = danas[0]
        e = B.procena(k, x['dan'], r['team'], r['opp'])
        if not e or e['n'] < 2:
            continue
        sx = e['s'][x['s']]
        pm = verovatnoca_preko(x['s'], sx['mu'], sx['var'], x['l'])
        tr = (1 / x['o']) / (1 / x['u'] + 1 / x['o'])
        y = 1 if r[x['s']] > x['l'] else 0
        rez.append(dict(x, k=k, kolo=r['r'], mu=sx['mu'], var=sx['var'], pm=round(pm, 4), tr=round(tr, 4),
                        ishod=r[x['s']], preko=y, marza=round(1 / x['u'] + 1 / x['o'] - 1, 4)))
    print('granica', len(rez), 'igrač nije igrao', nije_igrao, 'nepoznatih imena', sum(nema_igraca.values()))
    if nema_igraca:
        print('  nepoznati:', nema_igraca.most_common(15))

    linije = []
    def L(t=''):
        linije.append(t)

    def blok(naslov, R):
        if not R:
            return
        n = len(R)
        llm = sum(ll(r['pm'], r['preko']) for r in R) / n
        llt = sum(ll(r['tr'], r['preko']) for r in R) / n
        llb = sum(ll((r['pm'] + r['tr']) / 2, r['preko']) for r in R) / n
        brm = sum((r['pm'] - r['preko']) ** 2 for r in R) / n
        brt = sum((r['tr'] - r['preko']) ** 2 for r in R) / n
        stv = sum(r['preko'] for r in R) / n
        L(f'| {naslov} | {n} | {stv:.1%} | {sum(r["pm"] for r in R)/n:.1%} | {sum(r["tr"] for r in R)/n:.1%} | {llm:.4f} | {llt:.4f} | {llb:.4f} | {brm:.4f} | {brt:.4f} |')

    zag = '| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |\n|---|---|---|---|---|---|---|---|---|---|'
    L('# Provera modela raspona na ponudama')
    L()
    L(f'Parametri: {model.PAR.get("_podeseno", "podrazumevani")}. Ponude: {", ".join(sorted({r["izvor"] for r in rez}))}, '
      f'{min(r["dan"] for r in rez)} do {max(r["dan"] for r in rez)}. Granica sa ishodom: {len(rez)} (igrač nije igrao: {nije_igrao}, ne računa se).')
    L()
    L('Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).')
    L()
    L('## Tačnost verovatnoća')
    L()
    L(zag)
    blok('sve', rez)
    blok('kola 4 do 6 (u periodu podešavanja)', [r for r in rez if r['kolo'] <= 6])
    blok('kola 7 do 9 (van podešavanja)', [r for r in rez if r['kolo'] >= 7])
    for s, ime in (('P', 'poeni'), ('S', 'skokovi'), ('A', 'asistencije')):
        blok(ime, [r for r in rez if r['s'] == s])
    for izv in sorted({r['izvor'] for r in rez}):
        blok(izv, [r for r in rez if r['izvor'] == izv])
    L()

    L('## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko')
    L()
    L('| model kaže preko | granica | stvarno preko | kvote kažu preko |')
    L('|---|---|---|---|')
    for a, b in ((0, .2), (.2, .3), (.3, .4), (.4, .5), (.5, .6), (.6, .7), (.7, .8), (.8, 1.01)):
        R = [r for r in rez if a <= r['pm'] < b]
        if R:
            L(f'| {a:.0%} do {min(b,1):.0%} | {len(R)} | {sum(r["preko"] for r in R)/len(R):.1%} | {sum(r["tr"] for r in R)/len(R):.1%} |')
    L()

    L('## Razlika model minus kvote: da li prati ishod')
    L()
    L('Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.')
    L()
    L('| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |')
    L('|---|---|---|---|---|')
    for a, b in ((-1, -.15), (-.15, -.08), (-.08, -.03), (-.03, .03), (.03, .08), (.08, .15), (.15, 1)):
        R = [r for r in rez if a <= r['pm'] - r['tr'] < b]
        if R:
            st = sum(r['preko'] for r in R) / len(R); tr = sum(r['tr'] for r in R) / len(R)
            se = math.sqrt(max(tr * (1 - tr), 1e-6) / len(R))
            L(f'| {a:+.0%} do {b:+.0%} | {len(R)} | {tr:.1%} | {st:.1%} | {st-tr:+.1%} (±{se:.1%}) |')
    L()

    L('## Osnova bez modela: uvek ista strana')
    L()
    L('Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.')
    L()
    L('| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |')
    L('|---|---|---|---|---|')
    for s, ime in (('sve', 'sve'), ('P', 'poeni'), ('S', 'skokovi'), ('A', 'asistencije')):
        R = [r for r in rez if s == 'sve' or r['s'] == s]
        if R:
            ui = sum((r['u'] - 1) if r['preko'] == 0 else -1 for r in R) / len(R)
            up = sum((r['o'] - 1) if r['preko'] == 1 else -1 for r in R) / len(R)
            L(f'| {ime} | {len(R)} | {ui:+.1%} | {up:+.1%} | {sum(r["marza"] for r in R)/len(R):.1%} |')
    L()
    L('Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.')
    L()
    L('| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |')
    L('|---|---|---|---|---|')
    for s, ime in (('sve', 'sve'), ('P', 'poeni'), ('S', 'skokovi'), ('A', 'asistencije')):
        R = [r for r in rez if s == 'sve' or r['s'] == s]
        da = [r for r in R if (1 - r['pm']) * r['u'] - 1 > 0.05]
        ne = [r for r in R if not ((1 - r['pm']) * r['u'] - 1 > 0.05)]
        f = lambda X: sum((r['u'] - 1) if r['preko'] == 0 else -1 for r in X) / len(X) if X else 0
        L(f'| {ime} | {len(da)} | {f(da):+.1%} | {len(ne)} | {f(ne):+.1%} |')
    L()

    L('## Da se igralo po modelu: ravan ulog, jedna strana po granici')
    L()
    L('Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.')
    L()
    L('| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |')
    L('|---|---|---|---|---|---|---|')
    for prag in (0.0, 0.05, 0.10, 0.15):
        for strana in ('preko', 'ispod', 'obe'):
            for s in ('sve', 'P', 'S', 'A'):
                igr = []
                for r in rez:
                    if s != 'sve' and r['s'] != s:
                        continue
                    evo = r['pm'] * r['o'] - 1; evu = (1 - r['pm']) * r['u'] - 1
                    if evo >= evu and evo > prag and strana in ('preko', 'obe'):
                        igr.append((r['o'], r['preko'] == 1))
                    elif evu > evo and evu > prag and strana in ('ispod', 'obe'):
                        igr.append((r['u'], r['preko'] == 0))
                if not igr:
                    continue
                dob = sum((k - 1) if w else -1 for k, w in igr)
                if s == 'sve' or prag == 0.05:
                    L(f'| {prag:.0%} | {strana} | {s} | {len(igr)} | {sum(w for _, w in igr)} | {sum(k for k, _ in igr)/len(igr):.2f} | {dob/len(igr):+.1%} |')
    L()

    # raspon na svim učinicima kola 7 do 9
    L('## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)')
    L()
    pok = collections.defaultdict(lambda: [0, 0, 0])
    for r in B.rows:
        if r['r'] < 7:
            continue
        e = B.procena(r['k'], r['dan'], r['team'], r['opp'])
        if not e or e['n'] < 2:
            continue
        for s in 'PSA':
            q10, q25, q50, q75, q90 = percentili(e['s'][s]['mu'], e['s'][s]['var'])
            x = r[s]; a = pok[s]
            a[0] += 1; a[1] += q25 <= x <= q75; a[2] += q10 <= x <= q90
    L('| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |')
    L('|---|---|---|---|')
    for s, ime in (('P', 'poeni'), ('S', 'skokovi'), ('A', 'asistencije')):
        a = pok[s]
        if a[0]:
            L(f'| {ime} | {a[0]} | {a[1]/a[0]:.1%} | {a[2]/a[0]:.1%} |')
    L()
    L('Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.')

    os.makedirs(os.path.join(PROCENE, 'provera'), exist_ok=True)
    with open(os.path.join(PROCENE, 'provera', 'izvestaj.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(linije) + '\n')
    sacuvaj(os.path.join(PROCENE, 'provera', 'granice.json'), rez, kompaktno=True)
    print('\n'.join(linije))


if __name__ == '__main__':
    main()
