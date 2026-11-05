# Minuti tima (praćenje, nije uvedeno)

Povod: MAD–PAN 4.11. Model je za PAN očekivao ukupno 244 minuta (računao je i igrače sa klupe koji nisu ušli), a prva postava je igrala više nego što je model očekivao.

Provera 5.11. na kolima 5 do 10 (1.753 granice iz `granice.json`, skripta u istoriji razgovora):

| varijanta | greška minuta | pristrasnost minuta | log gubitak (spojeno) | minusi (≥53%) | povraćaj svih |
|---|---|---|---|---|---|
| bez promene | 4,38 | −0,72 | 0,6830 | 868, 57,9% | +6,8% |
| srazmerno na 200 | 4,92 | −2,62 | 0,6843 | 1147, 57,9% | +8,8% |
| na 200 uz učešće (ko koliko često igra) | 4,55 | −1,56 | 0,6831 | 1000, 58,3% | +9,0% |

Zaključak: svođenje na 200 pogoršava procene (igrači iz ponude već imaju skoro tačne minute; višak dolaze od klupe).
Ne uvodi se (Nikola, 5.11.). Signal koji vredi pratiti: zbir očekivanih minuta uz učešće po timu i MINUS predlozi:

| zbir (uz učešće) | minusa | prošlo | povraćaj |
|---|---|---|---|
| ispod 205 | 356 | 59,8% | +9,5% |
| 205 do 225 | 465 | 57,4% | +5,4% |
| preko 225 | 47 | 48,9% | −10,1% |

Mogući pravilo za kasnije: tim sa zbirom preko 225 bez MINUS predloga. Prati se posle svakog kola
(`minuti_tima_<datum>.json` čuva zbirove pre utakmica). 5.11.: nijedan tim preko 225 (najviše BAR 218,6).
