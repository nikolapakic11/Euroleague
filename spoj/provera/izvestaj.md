# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 4045 (admiral, maxbet, mozzart, soccerbet), kola 4-11. Čist test (posle podešavanja minus-modela): kola 8-11. Rang se računa unutar dana.

## Admiral, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1103 | 53.1% | 1.92 | +1.2% |
| samo minus-model, najjačih 30% dana | 335 | 55.2% | 1.93 | +5.9% |
| samo procene, najjačih 30% dana | 335 | 58.2% | 1.96 | +14.0% |
| **oba se slažu (oba u najjačih 30%)** | 146 | 63.0% | 1.98 | +23.6% |
| minus da, procene ne | 189 | 49.2% | 1.90 | -7.8% |
| procene da, minus ne | 189 | 54.5% | 1.95 | +6.6% |

## Admiral, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1103 | 46.9% | 1.88 | -12.7% |
| minus-model okrenut, najjačih 30% ka preko | 327 | 47.7% | 1.90 | -9.6% |
| procene, najjačih 30% ka preko | 327 | 48.6% | 1.92 | -8.2% |
| oba se slažu za preko | 125 | 46.4% | 1.94 | -10.3% |

## Sve kladionice, kola 8-11: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 2743 | 54.2% | 1.92 | +2.9% |
| samo minus-model, najjačih 30% dana | 828 | 59.3% | 1.92 | +12.9% |
| samo procene, najjačih 30% dana | 828 | 59.5% | 1.96 | +16.1% |
| **oba se slažu (oba u najjačih 30%)** | 351 | 65.2% | 1.96 | +26.8% |
| minus da, procene ne | 477 | 54.9% | 1.89 | +2.7% |
| procene da, minus ne | 477 | 55.3% | 1.95 | +8.3% |

## Sve kladionice, kola 8-11: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 2743 | 45.8% | 1.88 | -15.2% |
| minus-model okrenut, najjačih 30% ka preko | 820 | 47.7% | 1.89 | -10.1% |
| procene, najjačih 30% ka preko | 820 | 48.5% | 1.92 | -8.4% |
| oba se slažu za preko | 333 | 45.9% | 1.94 | -11.6% |

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
| sve | 1041 | 52.4% | 1.94 | +1.3% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 261 | 56.3% | 1.77 | -0.4% |
| ranije, po vrednosti (verovatnoća × kvota) | 261 | 54.0% | 1.98 | +6.5% |
| novo: + 0,30·procene, po verovatnoći | 261 | 56.3% | 1.82 | +2.4% |
| **novo: + 0,30·procene, po vrednosti** | 261 | 56.7% | 2.01 | +13.4% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-11

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 180 | 62.2% | 1.88 | +16.8% |
| **minus-model se slaže (msig ≥ 0.35)** | 115 | 64.3% | 1.87 | +19.8% |
| izbačeni (minus-model se ne slaže) | 65 | 58.5% | 1.89 | +11.6% |

