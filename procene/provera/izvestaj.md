# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-06. Granica sa ishodom: 3059 (igrač nije igrao: 161, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 3059 | 45.6% | 42.3% | 50.7% | 0.6953 | 0.6887 | 0.6827 | 0.2502 | 0.2478 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 2219 | 46.8% | 42.1% | 50.6% | 0.7003 | 0.6864 | 0.6836 | 0.2524 | 0.2467 |
| poeni | 1569 | 46.5% | 41.9% | 50.1% | 0.6957 | 0.6917 | 0.6855 | 0.2506 | 0.2493 |
| skokovi | 870 | 46.1% | 43.3% | 51.5% | 0.7009 | 0.6847 | 0.6833 | 0.2529 | 0.2458 |
| asistencije | 620 | 42.6% | 41.8% | 51.1% | 0.6866 | 0.6869 | 0.6746 | 0.2453 | 0.2469 |
| admiral | 1998 | 44.8% | 42.2% | 50.7% | 0.6943 | 0.6918 | 0.6836 | 0.2498 | 0.2493 |
| maxbet | 446 | 48.0% | 42.6% | 50.7% | 0.7096 | 0.6828 | 0.6860 | 0.2565 | 0.2449 |
| mozzart | 237 | 47.3% | 43.3% | 50.7% | 0.6951 | 0.6824 | 0.6805 | 0.2499 | 0.2446 |
| soccerbet | 378 | 45.5% | 42.0% | 50.6% | 0.6842 | 0.6837 | 0.6752 | 0.2450 | 0.2453 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 46 | 47.8% | 47.3% |
| 20% do 30% | 282 | 35.1% | 48.4% |
| 30% do 40% | 986 | 42.5% | 49.4% |
| 40% do 50% | 1043 | 47.1% | 50.9% |
| 50% do 60% | 554 | 48.4% | 52.7% |
| 60% do 70% | 125 | 64.8% | 55.0% |
| 70% do 80% | 22 | 59.1% | 58.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 780 | 51.8% | 42.9% | -8.9% (±1.8%) |
| -15% do -8% | 851 | 50.9% | 44.3% | -6.6% (±1.7%) |
| -8% do -3% | 529 | 50.0% | 44.4% | -5.6% (±2.2%) |
| -3% do +3% | 532 | 50.1% | 50.6% | +0.5% (±2.2%) |
| +3% do +8% | 215 | 50.1% | 50.2% | +0.1% (±3.4%) |
| +8% do +15% | 121 | 49.5% | 48.8% | -0.8% (±4.5%) |
| +15% do +100% | 31 | 46.8% | 35.5% | -11.3% (±9.0%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 3059 | +3.5% | -15.8% | 6.7% |
| poeni | 1569 | +2.3% | -11.6% | 5.0% |
| skokovi | 870 | +2.4% | -18.0% | 8.5% |
| asistencije | 620 | +8.0% | -23.5% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 1855 | +8.5% | 1204 | -4.3% |
| poeni | 998 | +9.5% | 571 | -10.2% |
| skokovi | 488 | +4.2% | 382 | -0.0% |
| asistencije | 369 | +11.5% | 251 | +2.8% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 360 | 173 | 1.92 | -10.3% |
| 0% | ispod | sve | 2138 | 1194 | 1.94 | +7.6% |
| 0% | obe | sve | 2498 | 1367 | 1.94 | +5.0% |
| 5% | preko | sve | 221 | 102 | 1.95 | -11.7% |
| 5% | preko | P | 112 | 56 | 1.93 | -3.8% |
| 5% | preko | S | 55 | 23 | 1.99 | -18.5% |
| 5% | preko | A | 54 | 23 | 1.96 | -21.1% |
| 5% | ispod | sve | 1855 | 1038 | 1.95 | +8.5% |
| 5% | ispod | P | 998 | 567 | 1.93 | +9.5% |
| 5% | ispod | S | 488 | 257 | 1.99 | +4.2% |
| 5% | ispod | A | 369 | 214 | 1.93 | +11.5% |
| 5% | obe | sve | 2076 | 1140 | 1.95 | +6.4% |
| 5% | obe | P | 1110 | 623 | 1.93 | +8.2% |
| 5% | obe | S | 543 | 280 | 1.99 | +1.9% |
| 5% | obe | A | 423 | 237 | 1.94 | +7.4% |
| 10% | preko | sve | 138 | 56 | 1.99 | -21.9% |
| 10% | ispod | sve | 1559 | 868 | 1.96 | +8.9% |
| 10% | obe | sve | 1697 | 924 | 1.96 | +6.4% |
| 15% | preko | sve | 76 | 30 | 2.08 | -20.5% |
| 15% | ispod | sve | 1211 | 695 | 1.97 | +12.8% |
| 15% | obe | sve | 1287 | 725 | 1.98 | +10.9% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 830 | 54.2% | 83.7% |
| skokovi | 830 | 62.0% | 87.6% |
| asistencije | 830 | 75.4% | 91.0% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
