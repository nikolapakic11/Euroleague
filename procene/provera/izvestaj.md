# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-12. Granica sa ishodom: 4045 (igrač nije igrao: 189, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 4045 | 45.0% | 41.8% | 50.6% | 0.6933 | 0.6904 | 0.6822 | 0.2491 | 0.2486 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 3205 | 45.7% | 41.5% | 50.5% | 0.6962 | 0.6893 | 0.6828 | 0.2504 | 0.2481 |
| poeni | 2104 | 45.9% | 41.4% | 50.1% | 0.6902 | 0.6910 | 0.6823 | 0.2481 | 0.2489 |
| skokovi | 1143 | 45.2% | 42.8% | 51.3% | 0.7015 | 0.6918 | 0.6871 | 0.2532 | 0.2493 |
| asistencije | 798 | 42.4% | 41.2% | 51.1% | 0.6897 | 0.6871 | 0.6750 | 0.2459 | 0.2470 |
| admiral | 2227 | 44.8% | 42.0% | 50.7% | 0.6943 | 0.6926 | 0.6839 | 0.2497 | 0.2497 |
| maxbet | 684 | 46.6% | 41.9% | 50.7% | 0.7054 | 0.6888 | 0.6869 | 0.2545 | 0.2478 |
| mozzart | 448 | 46.4% | 41.9% | 50.5% | 0.6972 | 0.6893 | 0.6841 | 0.2507 | 0.2481 |
| soccerbet | 686 | 43.3% | 40.9% | 50.4% | 0.6754 | 0.6858 | 0.6711 | 0.2408 | 0.2464 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 60 | 51.7% | 46.5% |
| 20% do 30% | 427 | 31.4% | 48.2% |
| 30% do 40% | 1309 | 42.9% | 49.4% |
| 40% do 50% | 1389 | 47.4% | 50.9% |
| 50% do 60% | 700 | 47.9% | 53.0% |
| 60% do 70% | 137 | 62.8% | 55.2% |
| 70% do 80% | 22 | 59.1% | 58.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 1088 | 51.7% | 41.0% | -10.7% (±1.5%) |
| -15% do -8% | 1107 | 50.9% | 44.7% | -6.2% (±1.5%) |
| -8% do -3% | 736 | 50.0% | 45.1% | -4.9% (±1.8%) |
| -3% do +3% | 690 | 49.7% | 50.3% | +0.6% (±1.9%) |
| +3% do +8% | 270 | 49.7% | 47.8% | -1.9% (±3.0%) |
| +8% do +15% | 123 | 49.5% | 49.6% | +0.0% (±4.5%) |
| +15% do +100% | 31 | 46.8% | 35.5% | -11.3% (±9.0%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 4045 | +4.5% | -16.6% | 6.8% |
| poeni | 2104 | +3.1% | -12.8% | 5.2% |
| skokovi | 1143 | +4.3% | -18.5% | 8.5% |
| asistencije | 798 | +8.4% | -23.9% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 2491 | +8.7% | 1554 | -2.3% |
| poeni | 1367 | +8.7% | 737 | -7.2% |
| skokovi | 641 | +4.9% | 502 | +3.7% |
| asistencije | 483 | +14.0% | 315 | -0.3% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 414 | 200 | 1.93 | -9.4% |
| 0% | ispod | sve | 2877 | 1621 | 1.94 | +8.4% |
| 0% | obe | sve | 3291 | 1821 | 1.94 | +6.2% |
| 5% | preko | sve | 235 | 110 | 1.96 | -10.6% |
| 5% | preko | P | 121 | 63 | 1.93 | -0.1% |
| 5% | preko | S | 56 | 23 | 2.00 | -20.0% |
| 5% | preko | A | 58 | 24 | 1.97 | -23.3% |
| 5% | ispod | sve | 2491 | 1398 | 1.95 | +8.7% |
| 5% | ispod | P | 1367 | 772 | 1.93 | +8.7% |
| 5% | ispod | S | 641 | 339 | 1.99 | +4.9% |
| 5% | ispod | A | 483 | 287 | 1.94 | +14.0% |
| 5% | obe | sve | 2726 | 1508 | 1.95 | +7.1% |
| 5% | obe | P | 1488 | 835 | 1.93 | +8.0% |
| 5% | obe | S | 697 | 362 | 1.99 | +2.9% |
| 5% | obe | A | 541 | 311 | 1.94 | +10.0% |
| 10% | preko | sve | 140 | 58 | 1.98 | -20.3% |
| 10% | ispod | sve | 2098 | 1183 | 1.96 | +10.1% |
| 10% | obe | sve | 2238 | 1241 | 1.96 | +8.2% |
| 15% | preko | sve | 76 | 30 | 2.08 | -20.5% |
| 15% | ispod | sve | 1655 | 969 | 1.97 | +14.9% |
| 15% | obe | sve | 1731 | 999 | 1.98 | +13.4% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 999 | 54.6% | 83.6% |
| skokovi | 999 | 63.3% | 88.0% |
| asistencije | 999 | 75.3% | 91.3% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
