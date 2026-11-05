# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-05. Granica sa ishodom: 2300 (igrač nije igrao: 412, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 2300 | 46.0% | 41.7% | 50.6% | 0.6983 | 0.6885 | 0.6831 | 0.2515 | 0.2477 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 1460 | 48.1% | 41.2% | 50.5% | 0.7075 | 0.6849 | 0.6848 | 0.2556 | 0.2459 |
| poeni | 1147 | 47.5% | 41.1% | 50.1% | 0.7113 | 0.6910 | 0.6917 | 0.2578 | 0.2489 |
| skokovi | 665 | 44.7% | 43.1% | 51.5% | 0.6859 | 0.6874 | 0.6771 | 0.2462 | 0.2471 |
| asistencije | 488 | 44.1% | 41.3% | 50.8% | 0.6844 | 0.6841 | 0.6710 | 0.2436 | 0.2455 |
| admiral | 1819 | 44.9% | 42.0% | 50.7% | 0.6943 | 0.6918 | 0.6834 | 0.2498 | 0.2493 |
| maxbet | 270 | 49.3% | 41.7% | 50.6% | 0.7157 | 0.6767 | 0.6839 | 0.2590 | 0.2419 |
| mozzart | 83 | 51.8% | 40.6% | 50.0% | 0.7201 | 0.6794 | 0.6878 | 0.2611 | 0.2432 |
| soccerbet | 128 | 50.8% | 39.2% | 50.4% | 0.7027 | 0.6725 | 0.6745 | 0.2533 | 0.2398 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 40 | 45.0% | 47.5% |
| 20% do 30% | 236 | 39.4% | 48.7% |
| 30% do 40% | 778 | 42.7% | 49.6% |
| 40% do 50% | 757 | 46.4% | 50.9% |
| 50% do 60% | 369 | 50.7% | 52.3% |
| 60% do 70% | 101 | 61.4% | 54.6% |
| 70% do 80% | 18 | 72.2% | 57.4% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 648 | 51.6% | 44.6% | -7.0% (±2.0%) |
| -15% do -8% | 616 | 50.6% | 43.5% | -7.1% (±2.0%) |
| -8% do -3% | 377 | 50.1% | 44.3% | -5.8% (±2.6%) |
| -3% do +3% | 373 | 50.1% | 48.8% | -1.3% (±2.6%) |
| +3% do +8% | 172 | 50.1% | 52.3% | +2.2% (±3.8%) |
| +8% do +15% | 90 | 50.2% | 55.6% | +5.4% (±5.3%) |
| +15% do +100% | 24 | 47.5% | 45.8% | -1.6% (±10.2%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 2300 | +2.6% | -14.9% | 6.6% |
| poeni | 1147 | +0.4% | -9.4% | 4.7% |
| skokovi | 665 | +5.3% | -20.5% | 8.5% |
| asistencije | 488 | +4.4% | -20.4% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 1434 | +7.6% | 866 | -5.6% |
| poeni | 771 | +3.2% | 376 | -5.5% |
| skokovi | 377 | +13.3% | 288 | -5.1% |
| asistencije | 286 | +12.1% | 202 | -6.6% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 275 | 146 | 1.91 | -0.6% |
| 0% | ispod | sve | 1642 | 914 | 1.93 | +6.7% |
| 0% | obe | sve | 1917 | 1060 | 1.93 | +5.7% |
| 5% | preko | sve | 171 | 88 | 1.94 | -1.4% |
| 5% | preko | P | 86 | 42 | 1.93 | -5.5% |
| 5% | preko | S | 47 | 23 | 2.01 | -4.6% |
| 5% | preko | A | 38 | 23 | 1.87 | +12.2% |
| 5% | ispod | sve | 1434 | 802 | 1.94 | +7.6% |
| 5% | ispod | P | 771 | 415 | 1.92 | +3.2% |
| 5% | ispod | S | 377 | 218 | 1.98 | +13.3% |
| 5% | ispod | A | 286 | 169 | 1.92 | +12.1% |
| 5% | obe | sve | 1605 | 890 | 1.94 | +6.7% |
| 5% | obe | P | 857 | 457 | 1.92 | +2.3% |
| 5% | obe | S | 424 | 241 | 1.98 | +11.3% |
| 5% | obe | A | 324 | 192 | 1.91 | +12.1% |
| 10% | preko | sve | 100 | 48 | 1.97 | -7.3% |
| 10% | ispod | sve | 1219 | 666 | 1.95 | +5.9% |
| 10% | obe | sve | 1319 | 714 | 1.95 | +4.9% |
| 15% | preko | sve | 57 | 27 | 2.07 | -4.5% |
| 15% | ispod | sve | 982 | 548 | 1.96 | +8.7% |
| 15% | obe | sve | 1039 | 575 | 1.96 | +8.0% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 697 | 53.8% | 83.5% |
| skokovi | 697 | 62.1% | 87.2% |
| asistencije | 697 | 75.6% | 90.7% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
