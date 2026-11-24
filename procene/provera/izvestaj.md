# Provera modela raspona na ponudama

Parametri: kola 3-6, 836 učinaka, log ver -5417.3. Ponude: admiral, maxbet, mozzart, soccerbet, 2026-10-08 do 2026-11-20. Granica sa ishodom: 6739 (igrač nije igrao: 748, ne računa se).

Manji log gubitak i Brier znače bolje. „Kvote kažu“ je verovatnoća iz kvota bez marže. Kola 7 do 9 su van perioda podešavanja (pravi test).

## Tačnost verovatnoća

| skup | granica | stvarno preko | model kaže preko | kvote kažu preko | log gubitak model | log gubitak kvote | log gubitak pola-pola | Brier model | Brier kvote |
|---|---|---|---|---|---|---|---|---|---|
| sve | 6739 | 45.4% | 41.5% | 50.5% | 0.6932 | 0.6864 | 0.6802 | 0.2492 | 0.2466 |
| kola 4 do 6 (u periodu podešavanja) | 840 | 42.3% | 42.8% | 50.8% | 0.6822 | 0.6949 | 0.6802 | 0.2443 | 0.2508 |
| kola 7 do 9 (van podešavanja) | 5899 | 45.9% | 41.3% | 50.4% | 0.6948 | 0.6851 | 0.6803 | 0.2499 | 0.2460 |
| poeni | 3589 | 45.5% | 41.3% | 50.1% | 0.6892 | 0.6897 | 0.6814 | 0.2477 | 0.2483 |
| skokovi | 1837 | 45.5% | 42.2% | 50.9% | 0.6987 | 0.6835 | 0.6809 | 0.2517 | 0.2452 |
| asistencije | 1313 | 45.0% | 41.0% | 50.9% | 0.6968 | 0.6813 | 0.6763 | 0.2498 | 0.2441 |
| admiral | 2911 | 45.1% | 41.8% | 50.6% | 0.6944 | 0.6905 | 0.6830 | 0.2498 | 0.2487 |
| maxbet | 1363 | 46.5% | 41.6% | 50.6% | 0.7014 | 0.6854 | 0.6835 | 0.2529 | 0.2462 |
| mozzart | 826 | 46.4% | 41.7% | 50.3% | 0.6957 | 0.6850 | 0.6811 | 0.2501 | 0.2459 |
| soccerbet | 1639 | 44.6% | 40.7% | 50.3% | 0.6831 | 0.6804 | 0.6722 | 0.2445 | 0.2437 |

## Kalibracija: kad model kaže X% za preko, koliko puta je stvarno bilo preko

| model kaže preko | granica | stvarno preko | kvote kažu preko |
|---|---|---|---|
| 0% do 20% | 90 | 51.1% | 46.2% |
| 20% do 30% | 722 | 32.4% | 46.9% |
| 30% do 40% | 2254 | 43.1% | 49.3% |
| 40% do 50% | 2340 | 47.9% | 51.0% |
| 50% do 60% | 1059 | 48.8% | 53.1% |
| 60% do 70% | 240 | 62.5% | 55.5% |
| 70% do 80% | 33 | 63.6% | 56.3% |
| 80% do 100% | 1 | 100.0% | 57.3% |

## Razlika model minus kvote: da li prati ishod

Granice su podeljene po tome koliko model vidi veću verovatnoću za preko od kvota. Ako model nešto zna, u gornjim redovima stvarno preko treba da bude iznad onoga što kvote kažu, a u donjim ispod.

| model minus kvote (preko) | granica | kvote kažu preko | stvarno preko | razlika stvarno minus kvote |
|---|---|---|---|---|
| -100% do -15% | 1831 | 51.9% | 43.5% | -8.4% (±1.2%) |
| -15% do -8% | 1890 | 50.6% | 44.3% | -6.3% (±1.2%) |
| -8% do -3% | 1280 | 49.8% | 45.5% | -4.3% (±1.4%) |
| -3% do +3% | 1059 | 49.5% | 46.7% | -2.8% (±1.5%) |
| +3% do +8% | 423 | 49.2% | 52.0% | +2.8% (±2.4%) |
| +8% do +15% | 200 | 49.4% | 51.5% | +2.1% (±3.5%) |
| +15% do +100% | 56 | 47.5% | 46.4% | -1.1% (±6.7%) |

## Osnova bez modela: uvek ista strana

Da bi se videlo koliko model dodaje, ovo je ishod kad se bez ikakvog modela uvek uzme ista strana.

| stavka | granica | uvek ispod: povraćaj | uvek preko: povraćaj | prosečna marža |
|---|---|---|---|---|
| sve | 6739 | +3.1% | -16.1% | 6.9% |
| poeni | 3589 | +3.7% | -13.9% | 5.5% |
| skokovi | 1837 | +2.5% | -18.2% | 8.5% |
| asistencije | 1313 | +2.5% | -19.2% | 8.6% |

Model unutar ispod: povraćaj na granicama gde model kaže ispod (prednost iznad 5%) u odnosu na ostale granice gde se uzme ispod.

| stavka | model bira ispod: granica | povraćaj | ostale granice ispod: granica | povraćaj |
|---|---|---|---|---|
| sve | 4239 | +6.3% | 2500 | -2.3% |
| poeni | 2403 | +7.7% | 1186 | -4.5% |
| skokovi | 1042 | +3.4% | 795 | +1.3% |
| asistencije | 794 | +5.8% | 519 | -2.5% |

## Da se igralo po modelu: ravan ulog, jedna strana po granici

Igra se strana gde je model × kvota najveće, ako prelazi prag. Ovo je samo provera da li model hvata nešto što kvote ne hvataju, ne preporuka. Uz ovoliki broj granica slučaj lako pravi ±10%.

| prag prednosti | strana | stavka | igrano | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|---|---|
| 0% | preko | sve | 651 | 337 | 1.94 | -2.2% |
| 0% | ispod | sve | 4888 | 2706 | 1.93 | +5.9% |
| 0% | obe | sve | 5539 | 3043 | 1.93 | +5.0% |
| 5% | preko | sve | 379 | 193 | 1.97 | -2.4% |
| 5% | preko | P | 188 | 112 | 1.93 | +14.6% |
| 5% | preko | S | 101 | 40 | 2.03 | -23.8% |
| 5% | preko | A | 90 | 41 | 1.98 | -13.9% |
| 5% | ispod | sve | 4239 | 2338 | 1.95 | +6.3% |
| 5% | ispod | P | 2403 | 1345 | 1.94 | +7.7% |
| 5% | ispod | S | 1042 | 551 | 1.98 | +3.4% |
| 5% | ispod | A | 794 | 442 | 1.93 | +5.8% |
| 5% | obe | sve | 4618 | 2531 | 1.95 | +5.6% |
| 5% | obe | P | 2591 | 1457 | 1.94 | +8.2% |
| 5% | obe | S | 1143 | 591 | 1.99 | +1.0% |
| 5% | obe | A | 884 | 483 | 1.94 | +3.8% |
| 10% | preko | sve | 230 | 109 | 1.96 | -9.5% |
| 10% | ispod | sve | 3535 | 1957 | 1.96 | +7.5% |
| 10% | obe | sve | 3765 | 2066 | 1.96 | +6.5% |
| 15% | preko | sve | 140 | 61 | 2.01 | -14.6% |
| 15% | ispod | sve | 2806 | 1580 | 1.98 | +10.3% |
| 15% | obe | sve | 2946 | 1641 | 1.98 | +9.1% |

## Raspon: koliko učinaka upada u procenjeni raspon (svi igrači, kola 7 do 9)

| stavka | učinaka | u rasponu 25. do 75. percentil | u rasponu 10. do 90. percentil |
|---|---|---|---|
| poeni | 1498 | 55.7% | 83.3% |
| skokovi | 1498 | 63.4% | 88.2% |
| asistencije | 1498 | 74.7% | 91.7% |

Kod celih brojeva raspon sa krajevima uključenim prirodno hvata nešto više od 50% i 80%.
