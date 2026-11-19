# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 5474 (admiral, maxbet, mozzart, soccerbet), kola 4-12. Čist test (posle podešavanja minus-modela): kola 8-12. Rang se računa unutar dana.

## Admiral, kola 8-12: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1491 | 52.9% | 1.92 | +0.5% |
| samo minus-model, najjačih 30% dana | 452 | 54.2% | 1.93 | +3.4% |
| samo procene, najjačih 30% dana | 452 | 56.6% | 1.96 | +10.3% |
| **oba se slažu (oba u najjačih 30%)** | 192 | 58.9% | 1.97 | +14.8% |
| minus da, procene ne | 260 | 50.8% | 1.90 | -5.0% |
| procene da, minus ne | 260 | 55.0% | 1.96 | +7.1% |

## Admiral, kola 8-12: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1491 | 47.1% | 1.88 | -12.4% |
| minus-model okrenut, najjačih 30% ka preko | 441 | 47.4% | 1.90 | -10.4% |
| procene, najjačih 30% ka preko | 441 | 47.2% | 1.92 | -11.3% |
| oba se slažu za preko | 172 | 46.5% | 1.94 | -10.4% |

## Sve kladionice, kola 8-12: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 4172 | 53.7% | 1.92 | +1.4% |
| samo minus-model, najjačih 30% dana | 1258 | 57.1% | 1.91 | +7.8% |
| samo procene, najjačih 30% dana | 1258 | 57.1% | 1.96 | +10.6% |
| **oba se slažu (oba u najjačih 30%)** | 530 | 59.2% | 1.95 | +14.1% |
| minus da, procene ne | 728 | 55.5% | 1.88 | +3.2% |
| procene da, minus ne | 728 | 55.5% | 1.97 | +8.1% |

## Sve kladionice, kola 8-12: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 4172 | 46.3% | 1.88 | -14.6% |
| minus-model okrenut, najjačih 30% ka preko | 1247 | 47.8% | 1.89 | -10.5% |
| procene, najjačih 30% ka preko | 1247 | 46.6% | 1.92 | -12.7% |
| oba se slažu za preko | 515 | 45.8% | 1.94 | -12.6% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 5-7: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 833 | 55.7% | 1.94 | +7.7% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 211 | 63.0% | 1.77 | +12.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 211 | 59.7% | 1.97 | +17.3% |
| novo: + 0,30·procene, po verovatnoći | 211 | 61.6% | 1.83 | +12.3% |
| **novo: + 0,30·procene, po vrednosti** | 211 | 59.2% | 2.00 | +18.0% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 8-12: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 1412 | 52.0% | 1.94 | +0.2% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 356 | 56.7% | 1.76 | -0.0% |
| ranije, po vrednosti (verovatnoća × kvota) | 356 | 54.5% | 1.98 | +7.3% |
| novo: + 0,30·procene, po verovatnoći | 356 | 56.5% | 1.81 | +2.1% |
| **novo: + 0,30·procene, po vrednosti** | 356 | 54.8% | 2.01 | +9.2% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-12

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 358 | 60.1% | 1.87 | +12.0% |
| **minus-model se slaže (msig ≥ 0.35)** | 188 | 62.2% | 1.86 | +15.0% |
| izbačeni (minus-model se ne slaže) | 170 | 57.6% | 1.89 | +8.8% |

