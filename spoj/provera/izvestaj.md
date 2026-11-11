# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 3372 (admiral, maxbet, mozzart, soccerbet), kola 4-11. Čist test (posle podešavanja minus-modela): kola 8-11. Rang se računa unutar dana.

## Admiral, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 942 | 52.7% | 1.92 | +0.4% |
| samo minus-model, najjačih 30% dana | 286 | 53.8% | 1.94 | +3.5% |
| samo procene, najjačih 30% dana | 286 | 57.3% | 1.97 | +12.7% |
| **oba se slažu (oba u najjačih 30%)** | 126 | 61.9% | 1.98 | +21.9% |
| minus da, procene ne | 160 | 47.5% | 1.90 | -11.0% |
| procene da, minus ne | 160 | 53.8% | 1.95 | +5.5% |

## Admiral, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 942 | 47.3% | 1.88 | -11.8% |
| minus-model okrenut, najjačih 30% ka preko | 279 | 46.2% | 1.90 | -12.2% |
| procene, najjačih 30% ka preko | 279 | 49.8% | 1.92 | -6.2% |
| oba se slažu za preko | 107 | 46.7% | 1.94 | -9.9% |

## Sve kladionice, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 2070 | 53.4% | 1.92 | +1.4% |
| samo minus-model, najjačih 30% dana | 626 | 57.7% | 1.93 | +10.4% |
| samo procene, najjačih 30% dana | 626 | 58.5% | 1.97 | +15.0% |
| **oba se slažu (oba u najjačih 30%)** | 276 | 66.3% | 1.98 | +29.8% |
| minus da, procene ne | 350 | 50.9% | 1.89 | -4.9% |
| procene da, minus ne | 350 | 52.3% | 1.96 | +3.3% |

## Sve kladionice, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 2070 | 46.6% | 1.88 | -13.6% |
| minus-model okrenut, najjačih 30% ka preko | 619 | 46.5% | 1.90 | -12.0% |
| procene, najjačih 30% ka preko | 619 | 51.4% | 1.92 | -3.4% |
| oba se slažu za preko | 253 | 47.4% | 1.94 | -8.8% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 5-7: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 833 | 55.7% | 1.94 | +7.7% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 211 | 63.0% | 1.77 | +12.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 211 | 59.7% | 1.97 | +17.3% |
| novo: + 0,30·procene, po verovatnoći | 211 | 61.6% | 1.83 | +12.3% |
| **novo: + 0,30·procene, po vrednosti** | 211 | 59.2% | 2.00 | +18.0% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 8-11: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 889 | 52.0% | 1.95 | +0.6% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 223 | 54.3% | 1.77 | -3.9% |
| ranije, po vrednosti (verovatnoća × kvota) | 223 | 52.9% | 1.97 | +4.2% |
| novo: + 0,30·procene, po verovatnoći | 223 | 54.3% | 1.82 | -1.1% |
| **novo: + 0,30·procene, po vrednosti** | 223 | 57.4% | 2.01 | +15.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-11

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 155 | 61.3% | 1.88 | +15.3% |
| **minus-model se slaže (msig ≥ 0.35)** | 98 | 64.3% | 1.87 | +20.0% |
| izbačeni (minus-model se ne slaže) | 57 | 56.1% | 1.89 | +7.3% |

