# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 6739 (admiral, maxbet, mozzart, soccerbet), kola 4-13. Čist test (posle podešavanja minus-modela): kola 8-13. Rang se računa unutar dana.

## Admiral, kola 8-13: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1787 | 53.4% | 1.91 | +1.3% |
| samo minus-model, najjačih 30% dana | 541 | 54.5% | 1.93 | +4.0% |
| samo procene, najjačih 30% dana | 541 | 56.6% | 1.96 | +9.8% |
| **oba se slažu (oba u najjačih 30%)** | 230 | 58.7% | 1.96 | +13.9% |
| minus da, procene ne | 311 | 51.4% | 1.91 | -3.4% |
| procene da, minus ne | 311 | 55.0% | 1.95 | +6.7% |

## Admiral, kola 8-13: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1787 | 46.6% | 1.88 | -13.4% |
| minus-model okrenut, najjačih 30% ka preko | 529 | 45.6% | 1.90 | -13.8% |
| procene, najjačih 30% ka preko | 529 | 47.4% | 1.93 | -10.6% |
| oba se slažu za preko | 206 | 46.1% | 1.94 | -11.3% |

## Sve kladionice, kola 8-13: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 5437 | 54.1% | 1.91 | +2.0% |
| samo minus-model, najjačih 30% dana | 1638 | 57.1% | 1.92 | +7.9% |
| samo procene, najjačih 30% dana | 1638 | 56.8% | 1.95 | +9.5% |
| **oba se slažu (oba u najjačih 30%)** | 697 | 58.8% | 1.94 | +12.7% |
| minus da, procene ne | 941 | 55.9% | 1.90 | +4.4% |
| procene da, minus ne | 941 | 55.3% | 1.96 | +7.1% |

## Sve kladionice, kola 8-13: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 5437 | 45.9% | 1.88 | -15.3% |
| minus-model okrenut, najjačih 30% ka preko | 1625 | 45.5% | 1.89 | -14.8% |
| procene, najjačih 30% ka preko | 1625 | 47.9% | 1.93 | -9.9% |
| oba se slažu za preko | 668 | 46.0% | 1.94 | -12.5% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 5-7: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 833 | 55.7% | 1.94 | +7.7% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 211 | 63.0% | 1.77 | +12.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 211 | 59.7% | 1.97 | +17.3% |
| novo: + 0,30·procene, po verovatnoći | 211 | 61.6% | 1.83 | +12.3% |
| **novo: + 0,30·procene, po vrednosti** | 211 | 59.2% | 2.00 | +18.0% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 8-13: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 1694 | 52.7% | 1.94 | +1.3% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 427 | 57.8% | 1.76 | +1.3% |
| ranije, po vrednosti (verovatnoća × kvota) | 427 | 53.9% | 1.98 | +6.0% |
| novo: + 0,30·procene, po verovatnoći | 427 | 58.3% | 1.80 | +4.8% |
| **novo: + 0,30·procene, po vrednosti** | 427 | 55.3% | 2.01 | +9.9% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-13

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 514 | 59.1% | 1.86 | +9.9% |
| **minus-model se slaže (msig ≥ 0.35)** | 285 | 58.9% | 1.85 | +8.7% |
| izbačeni (minus-model se ne slaže) | 229 | 59.4% | 1.88 | +11.5% |

