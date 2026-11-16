"""Simulacija plana tiketa pre ponude: koliko se može očekivati za dati raspored dužina i uloga.

Pretpostavke (podesive): bazen od n igrača, ravnomerna raspodela, verovatnoća para p (prosek),
prosečna kvota q (raspon ±0.12), dnevni efekat (logit, sd), Admiral bonus po dužini i povraćaj po
kvoti ostalih parova (ispod 50 x1, 50–70 x2, 70–95 x3, od ~99 x5).
  python3 minusi/analiza/plan_sim.py
"""
import random, math, statistics as st, itertools, json, sys

BON = {4: .03, 5: .05, 6: .07, 7: .11, 8: .16, 9: .21, 10: .26, 11: .31, 12: .36, 13: .41, 14: .46}  # 12 potvrđeno (36%), 13-14 pretpostavka

def mult(o):
    return 1 if o < 50 else 2 if o < 70 else 3 if o < 96 else 5

def sim(plan, n=65, p=0.60, q=1.86, sd_dan=0.25, R=4000, seed=1):
    rnd = random.Random(seed)
    lg = math.log(p / (1 - p))
    ulog = sum(c * s for L, c, s in plan)
    out = []; win_t = []
    for _ in range(R):
        z = rnd.gauss(0, sd_dan)
        odds = [q + rnd.uniform(-.12, .12) for _ in range(n)]
        hit = [rnd.random() < 1 / (1 + math.exp(-(lg + z))) for _ in range(n)]
        # ravnomerno: igrači idu redom kroz izmešan spisak, tako da svako dobije približno isti broj mesta
        order = list(range(n)); rnd.shuffle(order); pos = 0
        tot = 0.0; wins = 0
        for L, c, s in plan:
            for _ in range(c):
                if pos + L > n:
                    rnd.shuffle(order); pos = 0
                t = order[pos:pos + L]; pos += L
                miss = [i for i in t if not hit[i]]
                o = math.prod(odds[i] for i in t)
                if not miss:
                    tot += s * o * (1 + BON.get(L, .26 + .05 * (L - 10))); wins += 1
                elif len(miss) == 1 and L >= 7:
                    tot += s * mult(o / odds[miss[0]])
        out.append(tot); win_t.append(wins)
    out.sort()
    return dict(ulog=ulog, prosek=st.mean(out), medijana=out[len(out) // 2], p10=out[len(out) // 10], p90=out[len(out) * 9 // 10],
                u_plusu=sum(x > ulog for x in out) / R, bez_dobitka=sum(w == 0 for w in win_t) / R, dobitnih=st.mean(win_t),
                pola_nazad=sum(x >= ulog / 2 for x in out) / R)

if __name__ == '__main__':
    planovi = {
        'A 40x8@100 + 40x10@50': [(8, 40, 100), (10, 40, 50)],
        'B A + 30x12@50': [(8, 40, 100), (10, 40, 50), (12, 30, 50)],
        'C A + 30x12@50 + 20x14@50': [(8, 40, 100), (10, 40, 50), (12, 30, 50), (14, 20, 50)],
        'D 50x8@100 + 60x10@50 + 40x12@50 + 20x14@50': [(8, 50, 100), (10, 60, 50), (12, 40, 50), (14, 20, 50)],
        'samo 12: 100x12@50': [(12, 100, 50)],
        'samo 14: 100x14@50': [(14, 100, 50)],
        'samo 8: 50x8@100': [(8, 50, 100)],
        'samo 10: 100x10@50': [(10, 100, 50)],
    }
    for p in (0.57, 0.60, 0.63):
        print(f'\n=== verovatnoća para {p:.2f} (kvota 1,86, bazen 65 igrača) ===')
        for nm, pl in planovi.items():
            r = sim(pl, p=p, R=3000)
            print(f"  {nm:44s} ulog {r['ulog']:6.0f} | prosek {r['prosek']/r['ulog']*100:5.0f}% | medijana {r['medijana']/r['ulog']*100:4.0f}% | "
                  f"u plusu {r['u_plusu']:.0%} | bar pola nazad {r['pola_nazad']:.0%} | bez ijednog dobitnog {r['bez_dobitka']:.0%} | dobitnih {r['dobitnih']:.2f}")
