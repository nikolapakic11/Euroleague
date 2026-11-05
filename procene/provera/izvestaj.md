# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-04. Granica sa ishodom: 2051 (igrač nije igrao: 661, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 2051 | 45.7% | 41.8% | 50.6% | 0.6983 | 0.6910 | 0.6843 | 0.2513 | 0.2489 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 1211 | 48.1% | 41.2% | 50.5% | 0.7094 | 0.6882 | 0.6871 | 0.2562 | 0.2476 |
| poeni | 1014 | 48.4% | 41.1% | 50.0% | 0.7160 | 0.6916 | 0.6941 | 0.2599 | 0.2492 |
| skokovi | 602 | 42.9% | 43.4% | 51.5% | 0.6794 | 0.6900 | 0.6756 | 0.2433 | 0.2484 |
| asistencije | 435 | 43.2% | 41.4% | 50.9% | 0.6830 | 0.6909 | 0.6732 | 0.2426 | 0.2488 |
| admiral | 1762 | 44.8% | 42.0% | 50.7% | 0.6942 | 0.6926 | 0.6836 | 0.2496 | 0.2497 |
| maxbet | 211 | 49.3% | 41.8% | 50.6% | 0.7181 | 0.6800 | 0.6861 | 0.2596 | 0.2435 |
| mozzart | 31 | 51.6% | 38.2% | 49.6% | 0.7210 | 0.6860 | 0.6869 | 0.2596 | 0.2465 |
| soccerbet | 47 | 59.6% | 37.5% | 50.1% | 0.7479 | 0.6828 | 0.6979 | 0.2723 | 0.2448 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 36 | 50.0% | 47.3% |
| 20% do 30% | 214 | 40.2% | 48.8% |
| 30% do 40% | 684 | 40.8% | 49.7% |
| 40% do 50% | 680 | 47.2% | 50.8% |
| 50% do 60% | 334 | 50.9% | 52.5% |
| 60% do 70% | 84 | 58.3% | 54.4% |
| 70% do 80% | 18 | 72.2% | 57.4% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 565 | 51.5% | 42.3% | -9.2% (±2.1%) |
| -15% do -8% | 560 | 50.6% | 42.9% | -7.8% (±2.1%) |
| -8% do -3% | 323 | 50.5% | 48.0% | -2.5% (±2.8%) |
| -3% do +3% | 355 | 50.0% | 48.5% | -1.6% (±2.7%) |
| +3% do +8% | 148 | 49.8% | 51.4% | +1.5% (±4.1%) |
| +8% do +15% | 76 | 50.2% | 57.9% | +7.7% (±5.7%) |
| +15% do +100% | 24 | 47.5% | 45.8% | -1.6% (±10.2%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 2051 | +3.4% | -15.2% | 6.6% |
| poeni | 1014 | -1.3% | -7.4% | 4.5% |
| skokovi | 602 | +8.9% | -23.6% | 8.5% |
| asistencije | 435 | +6.8% | -21.5% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 1278 | +9.2% | 773 | -6.3% |
| poeni | 685 | +1.0% | 329 | -6.2% |
| skokovi | 341 | +18.4% | 261 | -3.4% |
| asistencije | 252 | +19.3% | 183 | -10.4% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 237 | 126 | 1.92 | +0.3% |
| 0% | ispod | sve | 1459 | 820 | 1.93 | +8.0% |
| 0% | obe | sve | 1696 | 946 | 1.93 | +6.9% |
| 5% | preko | sve | 151 | 77 | 1.94 | -1.6% |
| 5% | preko | P | 76 | 37 | 1.93 | -6.3% |
| 5% | preko | S | 43 | 19 | 2.04 | -11.7% |
| 5% | preko | A | 32 | 21 | 1.83 | +23.0% |
| 5% | ispod | sve | 1278 | 725 | 1.94 | +9.2% |
| 5% | ispod | P | 685 | 361 | 1.92 | +1.0% |
| 5% | ispod | S | 341 | 206 | 1.98 | +18.4% |
| 5% | ispod | A | 252 | 158 | 1.92 | +19.3% |
| 5% | obe | sve | 1429 | 802 | 1.94 | +8.1% |
| 5% | obe | P | 761 | 398 | 1.92 | +0.3% |
| 5% | obe | S | 384 | 225 | 1.99 | +15.0% |
| 5% | obe | A | 284 | 179 | 1.91 | +19.7% |
| 10% | preko | sve | 88 | 44 | 1.97 | -2.5% |
| 10% | ispod | sve | 1083 | 608 | 1.95 | +8.8% |
| 10% | obe | sve | 1171 | 652 | 1.95 | +8.0% |
| 15% | preko | sve | 53 | 27 | 2.05 | +2.7% |
| 15% | ispod | sve | 871 | 499 | 1.96 | +11.6% |
| 15% | obe | sve | 924 | 526 | 1.96 | +11.1% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 655 | 53.4% | 83.4% |
| skokovi | 655 | 62.7% | 87.5% |
| asistencije | 655 | 76.2% | 91.0% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
