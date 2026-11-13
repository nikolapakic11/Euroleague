# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 4452 (admiral, maxbet, mozzart, soccerbet), kola 4-11. Čist test (posle podešavanja minus-modela): kola 8-11. Rang se računa unutar dana.

## Admiral, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1196 | 53.3% | 1.92 | +1.4% |
| samo minus-model, najjačih 30% dana | 363 | 55.4% | 1.93 | +6.1% |
| samo procene, najjačih 30% dana | 363 | 57.3% | 1.96 | +12.1% |
| **oba se slažu (oba u najjačih 30%)** | 158 | 60.1% | 1.97 | +17.8% |
| minus da, procene ne | 205 | 51.7% | 1.90 | -2.9% |
| procene da, minus ne | 205 | 55.1% | 1.95 | +7.7% |

## Admiral, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1196 | 46.7% | 1.88 | -13.0% |
| minus-model okrenut, najjačih 30% ka preko | 354 | 48.3% | 1.90 | -8.5% |
| procene, najjačih 30% ka preko | 354 | 47.7% | 1.92 | -9.9% |
| oba se slažu za preko | 138 | 45.7% | 1.94 | -11.5% |

## Sve kladionice, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 3150 | 54.2% | 1.92 | +2.7% |
| samo minus-model, najjačih 30% dana | 951 | 59.0% | 1.92 | +12.1% |
| samo procene, najjačih 30% dana | 951 | 58.5% | 1.96 | +13.8% |
| **oba se slažu (oba u najjačih 30%)** | 406 | 61.1% | 1.96 | +18.2% |
| minus da, procene ne | 545 | 57.4% | 1.90 | +7.6% |
| procene da, minus ne | 545 | 56.5% | 1.96 | +10.5% |

## Sve kladionice, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 3150 | 45.8% | 1.87 | -15.4% |
| minus-model okrenut, najjačih 30% ka preko | 942 | 48.3% | 1.89 | -9.2% |
| procene, najjačih 30% ka preko | 942 | 47.5% | 1.92 | -10.8% |
| oba se slažu za preko | 394 | 45.2% | 1.94 | -13.1% |

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
| sve | 1130 | 52.4% | 1.94 | +1.3% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 284 | 56.7% | 1.77 | +0.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 284 | 53.9% | 1.98 | +6.4% |
| novo: + 0,30·procene, po verovatnoći | 284 | 56.3% | 1.81 | +2.4% |
| **novo: + 0,30·procene, po vrednosti** | 284 | 56.0% | 2.01 | +12.0% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-11

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 192 | 62.0% | 1.88 | +16.4% |
| **minus-model se slaže (msig ≥ 0.35)** | 124 | 63.7% | 1.87 | +18.7% |
| izbačeni (minus-model se ne slaže) | 68 | 58.8% | 1.89 | +12.2% |

