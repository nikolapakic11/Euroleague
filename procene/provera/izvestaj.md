# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-19. Granica sa ishodom: 6250 (igrač nije igrao: 112, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 6250 | 45.0% | 41.7% | 50.5% | 0.6923 | 0.6873 | 0.6804 | 0.2487 | 0.2471 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 5410 | 45.4% | 41.5% | 50.5% | 0.6939 | 0.6862 | 0.6805 | 0.2494 | 0.2465 |
| poeni | 3320 | 45.2% | 41.4% | 50.1% | 0.6866 | 0.6904 | 0.6805 | 0.2464 | 0.2486 |
| skokovi | 1709 | 45.5% | 42.5% | 51.0% | 0.7039 | 0.6837 | 0.6838 | 0.2541 | 0.2453 |
| asistencije | 1221 | 43.5% | 41.4% | 50.8% | 0.6917 | 0.6842 | 0.6754 | 0.2472 | 0.2456 |
| admiral | 2795 | 44.9% | 41.9% | 50.6% | 0.6945 | 0.6912 | 0.6834 | 0.2498 | 0.2490 |
| maxbet | 1247 | 46.2% | 41.9% | 50.6% | 0.7015 | 0.6863 | 0.6842 | 0.2529 | 0.2466 |
| mozzart | 723 | 45.2% | 41.9% | 50.2% | 0.6919 | 0.6861 | 0.6800 | 0.2482 | 0.2465 |
| soccerbet | 1485 | 43.9% | 40.9% | 50.4% | 0.6806 | 0.6815 | 0.6718 | 0.2433 | 0.2443 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 86 | 53.5% | 46.1% |
| 20% do 30% | 634 | 31.5% | 47.1% |
| 30% do 40% | 2073 | 42.6% | 49.3% |
| 40% do 50% | 2181 | 47.0% | 51.0% |
| 50% do 60% | 1013 | 48.7% | 53.1% |
| 60% do 70% | 233 | 61.8% | 55.3% |
| 70% do 80% | 29 | 58.6% | 56.0% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 1657 | 51.8% | 42.5% | -9.3% (±1.2%) |
| -15% do -8% | 1745 | 50.7% | 43.8% | -7.0% (±1.2%) |
| -8% do -3% | 1209 | 49.9% | 45.4% | -4.4% (±1.4%) |
| -3% do +3% | 991 | 49.6% | 47.4% | -2.2% (±1.6%) |
| +3% do +8% | 401 | 49.3% | 50.4% | +1.1% (±2.5%) |
| +8% do +15% | 191 | 49.2% | 49.2% | +0.0% (±3.6%) |
| +15% do +100% | 56 | 47.5% | 46.4% | -1.1% (±6.7%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 6250 | +4.1% | -16.9% | 6.9% |
| poeni | 3320 | +4.4% | -14.5% | 5.5% |
| skokovi | 1709 | +2.6% | -18.3% | 8.5% |
| asistencije | 1221 | +5.6% | -21.7% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 3900 | +7.5% | 2350 | -1.6% |
| poeni | 2219 | +9.4% | 1101 | -5.7% |
| skokovi | 963 | +1.4% | 746 | +4.0% |
| asistencije | 718 | +10.0% | 503 | -0.8% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 620 | 310 | 1.94 | -5.8% |
| 0% | ispod | sve | 4492 | 2512 | 1.94 | +7.3% |
| 0% | obe | sve | 5112 | 2822 | 1.94 | +5.7% |
| 5% | preko | sve | 366 | 180 | 1.97 | -5.7% |
| 5% | preko | P | 184 | 108 | 1.93 | +12.9% |
| 5% | preko | S | 92 | 31 | 2.04 | -35.0% |
| 5% | preko | A | 90 | 41 | 1.98 | -13.9% |
| 5% | ispod | sve | 3900 | 2171 | 1.95 | +7.5% |
| 5% | ispod | P | 2219 | 1259 | 1.94 | +9.4% |
| 5% | ispod | S | 963 | 498 | 1.99 | +1.4% |
| 5% | ispod | A | 718 | 414 | 1.93 | +10.0% |
| 5% | obe | sve | 4266 | 2351 | 1.95 | +6.4% |
| 5% | obe | P | 2403 | 1367 | 1.94 | +9.6% |
| 5% | obe | S | 1055 | 529 | 1.99 | -1.7% |
| 5% | obe | A | 808 | 455 | 1.94 | +7.4% |
| 10% | preko | sve | 221 | 100 | 1.97 | -13.2% |
| 10% | ispod | sve | 3227 | 1808 | 1.96 | +9.1% |
| 10% | obe | sve | 3448 | 1908 | 1.96 | +7.6% |
| 15% | preko | sve | 139 | 60 | 2.02 | -15.1% |
| 15% | ispod | sve | 2557 | 1463 | 1.98 | +12.2% |
| 15% | obe | sve | 2696 | 1523 | 1.98 | +10.8% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 1409 | 55.8% | 83.5% |
| skokovi | 1409 | 63.7% | 88.3% |
| asistencije | 1409 | 74.7% | 91.6% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
