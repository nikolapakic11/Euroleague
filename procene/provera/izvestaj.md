# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, 2026-10-08 do 2026-10-30. Granica sa ishodom: 1907 (igrač nije igrao: 167, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 1907 | 44.9% | 42.1% | 50.7% | 0.6955 | 0.6914 | 0.6837 | 0.2502 | 0.2491 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 1067 | 47.0% | 41.7% | 50.6% | 0.7060 | 0.6887 | 0.6864 | 0.2549 | 0.2478 |
| poeni | 936 | 47.1% | 41.5% | 50.0% | 0.7121 | 0.6913 | 0.6928 | 0.2580 | 0.2491 |
| skokovi | 554 | 43.0% | 43.7% | 51.8% | 0.6838 | 0.6907 | 0.6779 | 0.2453 | 0.2488 |
| asistencije | 417 | 42.7% | 41.5% | 50.9% | 0.6740 | 0.6926 | 0.6709 | 0.2392 | 0.2497 |
| admiral | 1729 | 44.6% | 42.1% | 50.7% | 0.6934 | 0.6926 | 0.6834 | 0.2493 | 0.2497 |
| maxbet | 178 | 48.3% | 42.6% | 50.7% | 0.7160 | 0.6801 | 0.6860 | 0.2588 | 0.2436 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 30 | 43.3% | 47.1% |
| 20% do 30% | 190 | 39.5% | 48.9% |
| 30% do 40% | 615 | 40.7% | 49.7% |
| 40% do 50% | 654 | 46.0% | 50.8% |
| 50% do 60% | 322 | 50.3% | 52.4% |
| 60% do 70% | 81 | 56.8% | 54.2% |
| 70% do 80% | 14 | 64.3% | 59.5% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 507 | 51.5% | 41.6% | -9.9% (±2.2%) |
| -15% do -8% | 520 | 50.8% | 42.3% | -8.5% (±2.2%) |
| -8% do -3% | 310 | 50.5% | 47.7% | -2.8% (±2.8%) |
| -3% do +3% | 331 | 50.1% | 46.2% | -3.9% (±2.7%) |
| +3% do +8% | 143 | 49.8% | 51.7% | +1.9% (±4.2%) |
| +8% do +15% | 76 | 50.2% | 57.9% | +7.7% (±5.7%) |
| +15% do +100% | 20 | 47.0% | 35.0% | -12.0% (±11.2%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 1907 | +5.0% | -16.6% | 6.5% |
| poeni | 936 | +1.2% | -9.9% | 4.4% |
| skokovi | 554 | +9.4% | -23.9% | 8.6% |
| asistencije | 417 | +7.9% | -22.3% | 8.7% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 1176 | +10.4% | 731 | -3.6% |
| poeni | 621 | +3.1% | 315 | -2.7% |
| skokovi | 311 | +17.4% | 243 | -0.8% |
| asistencije | 244 | +20.0% | 173 | -9.2% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 231 | 120 | 1.92 | -1.8% |
| 0% | ispod | sve | 1348 | 764 | 1.94 | +9.2% |
| 0% | obe | sve | 1579 | 884 | 1.94 | +7.6% |
| 5% | preko | sve | 147 | 73 | 1.94 | -4.1% |
| 5% | preko | P | 72 | 33 | 1.93 | -11.7% |
| 5% | preko | S | 43 | 19 | 2.04 | -11.7% |
| 5% | preko | A | 32 | 21 | 1.83 | +23.0% |
| 5% | ispod | sve | 1176 | 672 | 1.94 | +10.4% |
| 5% | ispod | P | 621 | 334 | 1.92 | +3.1% |
| 5% | ispod | S | 311 | 184 | 2.00 | +17.4% |
| 5% | ispod | A | 244 | 154 | 1.92 | +20.0% |
| 5% | obe | sve | 1323 | 745 | 1.94 | +8.8% |
| 5% | obe | P | 693 | 367 | 1.92 | +1.6% |
| 5% | obe | S | 354 | 203 | 2.01 | +13.9% |
| 5% | obe | A | 276 | 175 | 1.91 | +20.4% |
| 10% | preko | sve | 84 | 40 | 1.98 | -6.9% |
| 10% | ispod | sve | 990 | 562 | 1.95 | +10.3% |
| 10% | obe | sve | 1074 | 602 | 1.95 | +9.0% |
| 15% | preko | sve | 49 | 23 | 2.06 | -4.5% |
| 15% | ispod | sve | 797 | 464 | 1.96 | +13.5% |
| 15% | obe | sve | 846 | 487 | 1.96 | +12.4% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 637 | 54.0% | 84.0% |
| skokovi | 637 | 62.5% | 87.3% |
| asistencije | 637 | 76.5% | 91.5% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
