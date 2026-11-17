# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-17. Granica sa ishodom: 5348 (igrač nije igrao: 93, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 5348 | 45.5% | 41.5% | 50.6% | 0.6967 | 0.6876 | 0.6825 | 0.2508 | 0.2472 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 4508 | 46.1% | 41.2% | 50.5% | 0.6994 | 0.6862 | 0.6829 | 0.2520 | 0.2466 |
| poeni | 2831 | 46.0% | 41.2% | 50.1% | 0.6914 | 0.6895 | 0.6822 | 0.2487 | 0.2482 |
| skokovi | 1477 | 45.5% | 42.4% | 51.2% | 0.7052 | 0.6874 | 0.6865 | 0.2550 | 0.2471 |
| asistencije | 1040 | 44.2% | 41.1% | 50.9% | 0.6989 | 0.6827 | 0.6777 | 0.2503 | 0.2449 |
| admiral | 2586 | 45.1% | 41.8% | 50.6% | 0.6964 | 0.6913 | 0.6843 | 0.2508 | 0.2491 |
| maxbet | 1038 | 47.0% | 41.6% | 50.7% | 0.7083 | 0.6868 | 0.6875 | 0.2561 | 0.2468 |
| mozzart | 532 | 46.2% | 41.7% | 50.4% | 0.7002 | 0.6889 | 0.6852 | 0.2521 | 0.2479 |
| soccerbet | 1192 | 44.6% | 40.6% | 50.5% | 0.6855 | 0.6797 | 0.6730 | 0.2456 | 0.2434 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 77 | 54.5% | 45.9% |
| 20% do 30% | 544 | 32.0% | 47.4% |
| 30% do 40% | 1830 | 43.2% | 49.4% |
| 40% do 50% | 1845 | 48.0% | 51.1% |
| 50% do 60% | 840 | 49.6% | 53.3% |
| 60% do 70% | 186 | 59.7% | 55.7% |
| 70% do 80% | 25 | 52.0% | 57.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 1461 | 51.9% | 42.8% | -9.1% (±1.3%) |
| -15% do -8% | 1519 | 50.7% | 45.1% | -5.6% (±1.3%) |
| -8% do -3% | 1001 | 49.8% | 47.4% | -2.4% (±1.6%) |
| -3% do +3% | 851 | 49.6% | 48.2% | -1.5% (±1.7%) |
| +3% do +8% | 319 | 49.6% | 47.0% | -2.6% (±2.8%) |
| +8% do +15% | 160 | 49.2% | 48.8% | -0.5% (±4.0%) |
| +15% do +100% | 37 | 47.5% | 29.7% | -17.8% (±8.2%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 5348 | +3.3% | -16.0% | 6.9% |
| poeni | 2831 | +2.8% | -13.0% | 5.4% |
| skokovi | 1477 | +3.3% | -18.3% | 8.5% |
| asistencije | 1040 | +4.3% | -20.6% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 3385 | +5.9% | 1963 | -1.3% |
| poeni | 1905 | +6.6% | 926 | -4.9% |
| skokovi | 847 | +3.0% | 630 | +3.9% |
| asistencije | 633 | +7.7% | 407 | -1.0% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 502 | 239 | 1.93 | -10.5% |
| 0% | ispod | sve | 3901 | 2143 | 1.94 | +5.4% |
| 0% | obe | sve | 4403 | 2382 | 1.94 | +3.6% |
| 5% | preko | sve | 290 | 137 | 1.96 | -9.7% |
| 5% | preko | P | 154 | 83 | 1.93 | +3.8% |
| 5% | preko | S | 67 | 24 | 2.00 | -30.6% |
| 5% | preko | A | 69 | 30 | 1.98 | -19.5% |
| 5% | ispod | sve | 3385 | 1854 | 1.95 | +5.9% |
| 5% | ispod | P | 1905 | 1056 | 1.93 | +6.6% |
| 5% | ispod | S | 847 | 442 | 1.99 | +3.0% |
| 5% | ispod | A | 633 | 356 | 1.93 | +7.7% |
| 5% | obe | sve | 3675 | 1991 | 1.95 | +4.7% |
| 5% | obe | P | 2059 | 1139 | 1.93 | +6.4% |
| 5% | obe | S | 914 | 466 | 1.99 | +0.5% |
| 5% | obe | A | 702 | 386 | 1.94 | +5.0% |
| 10% | preko | sve | 178 | 69 | 1.98 | -25.2% |
| 10% | ispod | sve | 2833 | 1566 | 1.96 | +7.7% |
| 10% | obe | sve | 3011 | 1635 | 1.97 | +5.8% |
| 15% | preko | sve | 108 | 40 | 2.05 | -25.8% |
| 15% | ispod | sve | 2252 | 1282 | 1.98 | +11.7% |
| 15% | obe | sve | 2360 | 1322 | 1.98 | +10.0% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 1258 | 55.4% | 83.5% |
| skokovi | 1258 | 63.4% | 87.8% |
| asistencije | 1258 | 74.6% | 91.0% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
