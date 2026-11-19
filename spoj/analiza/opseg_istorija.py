"""Opseg poena: provera na istoriji uz pretpostavku da Admiral kvote opsega računa samo iz granice (šablon sa 19.11.2026).
Za svako ranije kolo procena se pravi samo iz prethodnih kola (bez gledanja unapred).
  python3 spoj/analiza/opseg_istorija.py"""
import io, os, json, contextlib, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
src = open(os.path.join(R, 'spoj/analiza/an3.py'), encoding='utf8').read()
src = src[:src.index("print('  po stavci (p3")]
g = {'__file__': os.path.join(R, 'spoj/analiza/an3.py'), '__name__': 'an3_deo'}
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src, 'an3', 'exec'), g)
F = [x for x in g['F'] if x['s'] == 'P' and x.get('act') is not None and x.get('actmin', 1) > 0 and x['izvor'] == 'admiral']
for x in F:
    x['mix'] = (x['p3'] + 1 - x['pm']) / 2
    x['tr_u'] = 1 - x['tr']
# šablon kvota po granici (najčešća varijanta 19.11.)
SAB = {7.5: {(5, 10): 2.00, (10, 15): 4.00}, 8.5: {(5, 10): 2.10, (10, 15): 3.20, (0, 5): 3.40}, 9.5: {(5, 10): 2.40, (10, 15): 2.60},
       10.5: {(10, 15): 2.50, (5, 10): 2.50, (15, 20): 5.30}, 11.5: {(10, 15): 2.50, (5, 10): 3.10, (15, 20): 4.30},
       12.5: {(10, 15): 2.70, (5, 10): 3.60, (15, 20): 4.00}, 13.5: {(10, 15): 2.60, (15, 20): 3.50, (5, 10): 4.50},
       14.5: {(10, 15): 2.70, (15, 20): 3.10}, 15.5: {(10, 15): 3.00, (15, 20): 3.00, (20, 25): 5.30},
       17.5: {(15, 20): 3.00, (10, 15): 3.80, (20, 25): 4.00}, 18.5: {(15, 20): 3.00, (20, 25): 3.30, (10, 15): 4.20},
       20.5: {(20, 25): 3.10, (15, 20): 3.30, (25, 30): 5.00}}
def P(hist, l, p, a, b, gornja, kljuc):
    sl = [x for x in hist if abs(x['l'] - l) <= 3 and abs(x[kljuc] - p) <= 0.06]
    if len(sl) < 60: sl = [x for x in hist if abs(x['l'] - l) <= 4 and abs(x[kljuc] - p) <= 0.10]
    if len(sl) < 40: return None
    hi = b if gornja else b - 1
    return sum(a <= x['act'] <= hi for x in sl) / len(sl)
for gornja in (False, True):
    print(f"\n===== granica opsega: {'10–15 uključuje 15' if gornja else '10–15 znači 10–14'} =====")
    for kljuc, naziv in (('mix', 'naša procena (prosek spoja i procena)'), ('tr_u', 'samo kvote over/under (tržište)')):
        B = []
        for x in F:
            if x['kolo'] < 6 or x['l'] not in SAB: continue
            hist = [y for y in F if y['kolo'] < x['kolo']]
            for (a, b), k in SAB[x['l']].items():
                p = P(hist, x['l'], x[kljuc], a, b, gornja, kljuc)
                if p is None: continue
                hi = b if gornja else b - 1
                B.append(dict(ev=p * k - 1, k=k, hit=a <= x['act'] <= hi, kolo=x['kolo'], p=p))
        print(f"  -- {naziv}: {len(B)} mogućih opsega u kolima 6+ --")
        sve = sum(b['hit'] * b['k'] - 1 for b in B) / len(B)
        print(f"     svi opsezi naslepo: povrat {sve:+.1%}")
        for prag in (0.0, 0.10, 0.20, 0.30):
            S = [b for b in B if b['ev'] >= prag]
            if not S: continue
            roi = sum(b['hit'] * b['k'] - 1 for b in S) / len(S)
            hr = sum(b['hit'] for b in S) / len(S); pe = sum(b['p'] for b in S) / len(S)
            po_kolu = collections.defaultdict(list)
            for b in S: po_kolu[b['kolo']].append(b['hit'] * b['k'] - 1)
            plus = sum(sum(v) > 0 for v in po_kolu.values())
            print(f"     procenjena vrednost ≥{prag:+.0%}: n={len(S):4} | pogodak {hr:5.1%} (procena {pe:5.1%}) | prosečna kvota {sum(b['k'] for b in S)/len(S):.2f} | povrat {roi:+6.1%} | kola u plusu {plus}/{len(po_kolu)}")
