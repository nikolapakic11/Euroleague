# PLUS kad timu fali rotacija (12.11.2026)

Povod: Real 12.11. bez Campazza, Maledona, Decka, Jantunena i Garube, a sistem nije video nijedan plus.

Provera na spoj/analiza/F.json (kola 4–10, sve glavne granice; missmin = minuti rotacije koji fale tog dana, bez samog igrača).

Preko ukupno: 45% prema tržištu 50,5% (kladionice naginju preko, povraćaj oko −17%).

| skup | n | preko | tržište | povraćaj |
|---|---|---|---|---|
| missmin 40–60, sve stavke | 593 | 53,3% | 50,8% | −1,6% |
| missmin ≥ 40, P/A, pm > tržište | 53 | 73,6% | 50,8% | +34,5% |
| isto, uz pm ≥ 50% | 45 | 82,2% | – | +48,5% |
| missmin ≥ 35, P/A, pm > tržište | 67 | 64,2% | 50,1% | +17,1% |
| missmin < 40, P/A, pm > tržište | 388 | 48,7% | 49,8% | −8,6% |
| missmin ≥ 40, S | 259 | 44,4% | 51,1% | −20,1% |
| izostanci duži od 1 utakmice, 60+ min | 17 | 29% | 50% | – |

Po kolu (missmin ≥ 40, P/A, pm > tržište): 6: 2/2, 7: 60%, 8: 55%, 9: 88%, 10: 82%. Najviše iz Panatinaikosa (28 od 53), pa uzorak još nije širok.

Zašto Real nema plus: izostanci su stari (Deck od 3. kola, Maledon i Jantunen od 9, Campazzo od 1.11.), već su u poslednjim brojevima igrača, a kladionice su granice podigle iznad njih (Feliz 14,5 prema proseku 13,6, Luwawu-Cabarrot 12,5 prema 8,6, Pradilla 6,5 prema 4,7). Model za svakog igrača Reala vidi preko ispod tržišta.

Pravilo u procene/skripte/predlozi.py (PLUS_IZ_MIN = 40, PLUS_IZ_MAX = 2): poeni ili asistencije preko, timu fali bar 40 minuta rotacije (izveštaj o povredama + ko nije igrao poslednje dve), model procena pm ≥ 50% i iznad tržišta, kvota bar 1,60. Ulazi bez praga i forme, nivo nagoveštaj. Pratiti posle svakog kola; ako padne ispod 55% na 30+ novih granica, isključiti.
