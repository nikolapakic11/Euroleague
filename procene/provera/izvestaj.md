# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5403.9. Ponude: admiral, maxbet, 2026-10-08 do 2026-10-30. Granica sa ishodom: 1907 (igrač nije igrao: 23, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 1907 | 44.9% | 42.8% | 50.7% | 0.6983 | 0.6914 | 0.6856 | 0.2514 | 0.2491 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 43.1% | 50.8% | 0.6815 | 0.6949 | 0.6805 | 0.2440 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 1067 | 47.0% | 42.6% | 50.6% | 0.7115 | 0.6887 | 0.6896 | 0.2572 | 0.2478 |
| poeni | 936 | 47.1% | 42.1% | 50.0% | 0.7150 | 0.6913 | 0.6949 | 0.2592 | 0.2491 |
| skokovi | 554 | 43.0% | 44.8% | 51.8% | 0.6881 | 0.6907 | 0.6806 | 0.2472 | 0.2488 |
| asistencije | 417 | 42.7% | 41.8% | 50.9% | 0.6744 | 0.6926 | 0.6715 | 0.2394 | 0.2497 |
| admiral | 1729 | 44.6% | 42.8% | 50.7% | 0.6966 | 0.6926 | 0.6856 | 0.2507 | 0.2497 |
| maxbet | 178 | 48.3% | 43.2% | 50.7% | 0.7146 | 0.6801 | 0.6856 | 0.2577 | 0.2436 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 28 | 50.0% | 48.7% |
| 20% do 30% | 163 | 39.3% | 48.5% |
| 30% do 40% | 567 | 41.3% | 49.5% |
| 40% do 50% | 706 | 45.8% | 50.7% |
| 50% do 60% | 340 | 46.2% | 52.6% |
| 60% do 70% | 88 | 65.9% | 54.8% |
| 70% do 80% | 15 | 46.7% | 55.6% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 422 | 51.7% | 44.1% | -7.6% (±2.4%) |
| -15% do -8% | 528 | 50.7% | 41.5% | -9.3% (±2.2%) |
| -8% do -3% | 399 | 50.7% | 46.6% | -4.1% (±2.5%) |
| -3% do +3% | 300 | 50.1% | 48.0% | -2.1% (±2.9%) |
| +3% do +8% | 145 | 50.3% | 42.1% | -8.2% (±4.2%) |
| +8% do +15% | 94 | 49.3% | 60.6% | +11.3% (±5.2%) |
| +15% do +100% | 19 | 48.4% | 21.1% | -27.3% (±11.5%) |

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
| sve | 1128 | +9.7% | 779 | -1.8% |
| poeni | 613 | +3.9% | 323 | -4.1% |
| skokovi | 287 | +15.9% | 267 | +2.5% |
| asistencije | 228 | +17.6% | 189 | -3.9% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 241 | 122 | 1.93 | -5.0% |
| 0% | ispod | sve | 1332 | 753 | 1.94 | +9.1% |
| 0% | obe | sve | 1573 | 875 | 1.94 | +6.9% |
| 5% | preko | sve | 153 | 75 | 1.93 | -7.9% |
| 5% | preko | P | 67 | 29 | 1.93 | -17.0% |
| 5% | preko | S | 55 | 24 | 2.00 | -17.7% |
| 5% | preko | A | 31 | 22 | 1.82 | +29.0% |
| 5% | ispod | sve | 1128 | 639 | 1.94 | +9.7% |
| 5% | ispod | P | 613 | 332 | 1.92 | +3.9% |
| 5% | ispod | S | 287 | 166 | 2.01 | +15.9% |
| 5% | ispod | A | 228 | 141 | 1.92 | +17.6% |
| 5% | obe | sve | 1281 | 714 | 1.94 | +7.6% |
| 5% | obe | P | 680 | 361 | 1.92 | +1.9% |
| 5% | obe | S | 342 | 190 | 2.01 | +10.5% |
| 5% | obe | A | 259 | 163 | 1.91 | +19.0% |
| 10% | preko | sve | 93 | 45 | 1.98 | -6.8% |
| 10% | ispod | sve | 933 | 532 | 1.95 | +10.5% |
| 10% | obe | sve | 1026 | 577 | 1.95 | +9.0% |
| 15% | preko | sve | 52 | 21 | 2.03 | -21.5% |
| 15% | ispod | sve | 723 | 411 | 1.96 | +11.1% |
| 15% | obe | sve | 775 | 432 | 1.96 | +8.9% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 637 | 52.9% | 82.3% |
| skokovi | 637 | 63.7% | 87.1% |
| asistencije | 637 | 76.5% | 90.9% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
