# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-11. Granica sa ishodom: 3372 (igrač nije igrao: 585, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 3372 | 45.4% | 41.9% | 50.6% | 0.6926 | 0.6906 | 0.6822 | 0.2490 | 0.2487 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 2532 | 46.4% | 41.7% | 50.6% | 0.6960 | 0.6892 | 0.6829 | 0.2506 | 0.2480 |
| poeni | 1741 | 46.5% | 41.5% | 50.1% | 0.6931 | 0.6917 | 0.6840 | 0.2495 | 0.2493 |
| skokovi | 959 | 45.6% | 43.1% | 51.4% | 0.6987 | 0.6911 | 0.6855 | 0.2521 | 0.2489 |
| asistencije | 672 | 42.4% | 41.6% | 50.9% | 0.6824 | 0.6872 | 0.6729 | 0.2433 | 0.2471 |
| admiral | 2066 | 44.8% | 42.0% | 50.7% | 0.6934 | 0.6927 | 0.6835 | 0.2494 | 0.2497 |
| maxbet | 526 | 47.5% | 42.1% | 50.7% | 0.7051 | 0.6871 | 0.6861 | 0.2547 | 0.2470 |
| mozzart | 306 | 47.7% | 42.5% | 50.5% | 0.6954 | 0.6874 | 0.6831 | 0.2504 | 0.2471 |
| soccerbet | 474 | 44.1% | 41.1% | 50.5% | 0.6732 | 0.6877 | 0.6713 | 0.2401 | 0.2473 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 47 | 46.8% | 47.1% |
| 20% do 30% | 347 | 31.4% | 48.4% |
| 30% do 40% | 1082 | 42.9% | 49.4% |
| 40% do 50% | 1165 | 48.3% | 50.9% |
| 50% do 60% | 583 | 47.7% | 52.8% |
| 60% do 70% | 125 | 64.8% | 55.0% |
| 70% do 80% | 22 | 59.1% | 58.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 903 | 51.8% | 41.4% | -10.4% (±1.7%) |
| -15% do -8% | 923 | 50.9% | 43.8% | -7.1% (±1.6%) |
| -8% do -3% | 590 | 49.9% | 46.3% | -3.6% (±2.1%) |
| -3% do +3% | 576 | 49.8% | 51.6% | +1.7% (±2.1%) |
| +3% do +8% | 227 | 49.8% | 49.3% | -0.5% (±3.3%) |
| +8% do +15% | 122 | 49.5% | 49.2% | -0.4% (±4.5%) |
| +15% do +100% | 31 | 46.8% | 35.5% | -11.3% (±9.0%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 3372 | +3.9% | -15.9% | 6.8% |
| poeni | 1741 | +2.3% | -11.7% | 5.1% |
| skokovi | 959 | +3.7% | -18.1% | 8.5% |
| asistencije | 672 | +8.1% | -23.6% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 2074 | +9.6% | 1298 | -5.2% |
| poeni | 1138 | +9.5% | 603 | -11.1% |
| skokovi | 532 | +7.4% | 427 | -1.0% |
| asistencije | 404 | +12.7% | 268 | +1.1% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 369 | 178 | 1.93 | -9.7% |
| 0% | ispod | sve | 2382 | 1338 | 1.94 | +8.2% |
| 0% | obe | sve | 2751 | 1516 | 1.94 | +5.8% |
| 5% | preko | sve | 222 | 103 | 1.95 | -11.3% |
| 5% | preko | P | 112 | 56 | 1.93 | -3.8% |
| 5% | preko | S | 55 | 23 | 1.99 | -18.5% |
| 5% | preko | A | 55 | 24 | 1.96 | -19.1% |
| 5% | ispod | sve | 2074 | 1172 | 1.95 | +9.6% |
| 5% | ispod | P | 1138 | 646 | 1.93 | +9.5% |
| 5% | ispod | S | 532 | 289 | 1.99 | +7.4% |
| 5% | ispod | A | 404 | 237 | 1.93 | +12.7% |
| 5% | obe | sve | 2296 | 1275 | 1.95 | +7.6% |
| 5% | obe | P | 1250 | 702 | 1.93 | +8.3% |
| 5% | obe | S | 587 | 312 | 1.99 | +5.0% |
| 5% | obe | A | 459 | 261 | 1.93 | +8.9% |
| 10% | preko | sve | 138 | 56 | 1.99 | -21.9% |
| 10% | ispod | sve | 1747 | 991 | 1.96 | +10.9% |
| 10% | obe | sve | 1885 | 1047 | 1.96 | +8.5% |
| 15% | preko | sve | 76 | 30 | 2.08 | -20.5% |
| 15% | ispod | sve | 1373 | 805 | 1.97 | +15.3% |
| 15% | obe | sve | 1449 | 835 | 1.98 | +13.4% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 891 | 53.6% | 83.7% |
| skokovi | 891 | 63.0% | 88.0% |
| asistencije | 891 | 75.3% | 91.0% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
