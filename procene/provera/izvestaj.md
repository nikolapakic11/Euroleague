# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-06. Granica sa ishodom: 3182 (igrač nije igrao: 290, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 3182 | 45.9% | 42.1% | 50.7% | 0.6969 | 0.6901 | 0.6841 | 0.2510 | 0.2485 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 2342 | 47.2% | 41.9% | 50.6% | 0.7022 | 0.6884 | 0.6855 | 0.2534 | 0.2476 |
| poeni | 1641 | 46.5% | 41.7% | 50.1% | 0.6953 | 0.6922 | 0.6854 | 0.2505 | 0.2495 |
| skokovi | 901 | 46.7% | 43.4% | 51.5% | 0.7045 | 0.6874 | 0.6865 | 0.2547 | 0.2471 |
| asistencije | 640 | 43.1% | 41.6% | 51.0% | 0.6902 | 0.6885 | 0.6772 | 0.2470 | 0.2477 |
| admiral | 2026 | 45.0% | 42.1% | 50.7% | 0.6952 | 0.6923 | 0.6842 | 0.2502 | 0.2495 |
| maxbet | 473 | 48.4% | 42.4% | 50.7% | 0.7120 | 0.6853 | 0.6885 | 0.2578 | 0.2461 |
| mozzart | 263 | 48.3% | 42.9% | 50.6% | 0.7003 | 0.6857 | 0.6846 | 0.2525 | 0.2463 |
| soccerbet | 420 | 45.7% | 41.5% | 50.6% | 0.6861 | 0.6879 | 0.6779 | 0.2460 | 0.2474 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 47 | 46.8% | 47.1% |
| 20% do 30% | 311 | 34.7% | 48.5% |
| 30% do 40% | 1020 | 43.1% | 49.5% |
| 40% do 50% | 1092 | 48.1% | 50.8% |
| 50% do 60% | 564 | 47.9% | 52.8% |
| 60% do 70% | 125 | 64.8% | 55.0% |
| 70% do 80% | 22 | 59.1% | 58.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 829 | 51.8% | 43.2% | -8.7% (±1.7%) |
| -15% do -8% | 877 | 50.9% | 44.1% | -6.8% (±1.7%) |
| -8% do -3% | 561 | 49.9% | 45.3% | -4.6% (±2.1%) |
| -3% do +3% | 544 | 50.0% | 51.3% | +1.3% (±2.1%) |
| +3% do +8% | 219 | 50.0% | 51.1% | +1.1% (±3.4%) |
| +8% do +15% | 121 | 49.5% | 48.8% | -0.8% (±4.5%) |
| +15% do +100% | 31 | 46.8% | 35.5% | -11.3% (±9.0%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 3182 | +3.0% | -15.1% | 6.7% |
| poeni | 1641 | +2.3% | -11.6% | 5.0% |
| skokovi | 901 | +1.5% | -16.6% | 8.5% |
| asistencije | 640 | +6.9% | -22.1% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 1939 | +8.1% | 1243 | -5.0% |
| poeni | 1058 | +9.5% | 583 | -10.8% |
| skokovi | 500 | +3.6% | 401 | -1.2% |
| asistencije | 381 | +10.1% | 259 | +2.2% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 364 | 177 | 1.93 | -9.0% |
| 0% | ispod | sve | 2236 | 1243 | 1.94 | +7.1% |
| 0% | obe | sve | 2600 | 1420 | 1.94 | +4.9% |
| 5% | preko | sve | 221 | 102 | 1.95 | -11.7% |
| 5% | preko | P | 112 | 56 | 1.93 | -3.8% |
| 5% | preko | S | 55 | 23 | 1.99 | -18.5% |
| 5% | preko | A | 54 | 23 | 1.96 | -21.1% |
| 5% | ispod | sve | 1939 | 1080 | 1.95 | +8.1% |
| 5% | ispod | P | 1058 | 601 | 1.93 | +9.5% |
| 5% | ispod | S | 500 | 261 | 2.00 | +3.6% |
| 5% | ispod | A | 381 | 218 | 1.93 | +10.1% |
| 5% | obe | sve | 2160 | 1182 | 1.95 | +6.1% |
| 5% | obe | P | 1170 | 657 | 1.93 | +8.3% |
| 5% | obe | S | 555 | 284 | 2.00 | +1.4% |
| 5% | obe | A | 435 | 241 | 1.93 | +6.2% |
| 10% | preko | sve | 138 | 56 | 1.99 | -21.9% |
| 10% | ispod | sve | 1630 | 907 | 1.96 | +9.0% |
| 10% | obe | sve | 1768 | 963 | 1.97 | +6.5% |
| 15% | preko | sve | 76 | 30 | 2.08 | -20.5% |
| 15% | ispod | sve | 1273 | 732 | 1.97 | +13.2% |
| 15% | obe | sve | 1349 | 762 | 1.98 | +11.3% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 852 | 54.1% | 83.9% |
| skokovi | 852 | 62.0% | 87.8% |
| asistencije | 852 | 75.4% | 90.8% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
