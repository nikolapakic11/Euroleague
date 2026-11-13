# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-13. Granica sa ishodom: 4452 (igrač nije igrao: 52, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 4452 | 45.1% | 41.7% | 50.6% | 0.6947 | 0.6892 | 0.6823 | 0.2498 | 0.2481 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 3612 | 45.8% | 41.4% | 50.6% | 0.6976 | 0.6879 | 0.6828 | 0.2510 | 0.2474 |
| poeni | 2324 | 46.1% | 41.4% | 50.1% | 0.6903 | 0.6898 | 0.6818 | 0.2482 | 0.2483 |
| skokovi | 1256 | 45.1% | 42.7% | 51.2% | 0.7019 | 0.6911 | 0.6871 | 0.2534 | 0.2489 |
| asistencije | 872 | 42.4% | 41.0% | 51.1% | 0.6960 | 0.6852 | 0.6769 | 0.2487 | 0.2461 |
| admiral | 2320 | 44.8% | 41.9% | 50.6% | 0.6951 | 0.6922 | 0.6841 | 0.2501 | 0.2495 |
| maxbet | 777 | 46.6% | 41.8% | 50.7% | 0.7069 | 0.6882 | 0.6874 | 0.2553 | 0.2475 |
| mozzart | 532 | 46.2% | 41.7% | 50.4% | 0.7002 | 0.6889 | 0.6852 | 0.2521 | 0.2479 |
| soccerbet | 823 | 43.9% | 40.8% | 50.5% | 0.6785 | 0.6821 | 0.6707 | 0.2422 | 0.2446 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 64 | 54.7% | 46.4% |
| 20% do 30% | 465 | 30.5% | 47.8% |
| 30% do 40% | 1467 | 43.6% | 49.5% |
| 40% do 50% | 1531 | 47.0% | 50.9% |
| 50% do 60% | 752 | 48.8% | 53.1% |
| 60% do 70% | 147 | 62.6% | 55.6% |
| 70% do 80% | 25 | 52.0% | 57.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 1204 | 51.8% | 41.9% | -9.9% (±1.4%) |
| -15% do -8% | 1250 | 50.8% | 44.6% | -6.2% (±1.4%) |
| -8% do -3% | 809 | 50.0% | 45.9% | -4.1% (±1.8%) |
| -3% do +3% | 729 | 49.8% | 49.2% | -0.5% (±1.9%) |
| +3% do +8% | 294 | 49.7% | 47.6% | -2.0% (±2.9%) |
| +8% do +15% | 132 | 49.3% | 49.2% | -0.1% (±4.4%) |
| +15% do +100% | 34 | 47.0% | 32.4% | -14.7% (±8.6%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 4452 | +4.2% | -16.6% | 6.8% |
| poeni | 2324 | +2.7% | -12.7% | 5.3% |
| skokovi | 1256 | +4.3% | -18.7% | 8.5% |
| asistencije | 872 | +8.1% | -23.9% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 2783 | +7.6% | 1669 | -1.4% |
| poeni | 1534 | +7.4% | 790 | -6.5% |
| skokovi | 710 | +5.1% | 546 | +3.4% |
| asistencije | 539 | +11.4% | 333 | +2.7% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 447 | 216 | 1.93 | -9.1% |
| 0% | ispod | sve | 3208 | 1792 | 1.94 | +7.3% |
| 0% | obe | sve | 3655 | 2008 | 1.94 | +5.3% |
| 5% | preko | sve | 255 | 121 | 1.96 | -9.1% |
| 5% | preko | P | 136 | 74 | 1.93 | +4.7% |
| 5% | preko | S | 60 | 23 | 2.00 | -25.3% |
| 5% | preko | A | 59 | 24 | 1.98 | -24.6% |
| 5% | ispod | sve | 2783 | 1547 | 1.95 | +7.6% |
| 5% | ispod | P | 1534 | 857 | 1.93 | +7.4% |
| 5% | ispod | S | 710 | 376 | 1.99 | +5.1% |
| 5% | ispod | A | 539 | 314 | 1.93 | +11.4% |
| 5% | obe | sve | 3038 | 1668 | 1.95 | +6.2% |
| 5% | obe | P | 1670 | 931 | 1.93 | +7.2% |
| 5% | obe | S | 770 | 399 | 1.99 | +2.7% |
| 5% | obe | A | 598 | 338 | 1.94 | +7.8% |
| 10% | preko | sve | 153 | 62 | 1.99 | -21.8% |
| 10% | ispod | sve | 2336 | 1308 | 1.96 | +9.2% |
| 10% | obe | sve | 2489 | 1370 | 1.96 | +7.3% |
| 15% | preko | sve | 84 | 34 | 2.07 | -18.5% |
| 15% | ispod | sve | 1845 | 1066 | 1.97 | +13.5% |
| 15% | obe | sve | 1929 | 1100 | 1.98 | +12.1% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 1063 | 54.8% | 83.5% |
| skokovi | 1063 | 63.6% | 88.1% |
| asistencije | 1063 | 75.1% | 91.0% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
