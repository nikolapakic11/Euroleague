# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 7469 (admiral, maxbet, mozzart, soccerbet), kola 4-14. Čist test (posle podešavanja minus-modela): kola 8-14. Rang se računa unutar dana.

## Admiral, kola 8-14: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1963 | 53.9% | 1.92 | +2.5% |
| samo minus-model, najjačih 30% dana | 594 | 55.6% | 1.93 | +6.1% |
| samo procene, najjačih 30% dana | 594 | 57.1% | 1.95 | +10.8% |
| **oba se slažu (oba u najjačih 30%)** | 248 | 59.7% | 1.95 | +15.6% |
| minus da, procene ne | 346 | 52.6% | 1.91 | -0.7% |
| procene da, minus ne | 346 | 55.2% | 1.95 | +7.3% |

## Admiral, kola 8-14: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1963 | 46.1% | 1.88 | -14.3% |
| minus-model okrenut, najjačih 30% ka preko | 581 | 45.4% | 1.90 | -14.2% |
| procene, najjačih 30% ka preko | 581 | 47.3% | 1.92 | -11.0% |
| oba se slažu za preko | 221 | 46.6% | 1.93 | -10.6% |

## Sve kladionice, kola 8-14: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 6167 | 54.8% | 1.91 | +3.5% |
| samo minus-model, najjačih 30% dana | 1857 | 58.3% | 1.91 | +10.2% |
| samo procene, najjačih 30% dana | 1857 | 57.4% | 1.95 | +10.5% |
| **oba se slažu (oba u najjačih 30%)** | 774 | 59.8% | 1.94 | +14.4% |
| minus da, procene ne | 1083 | 57.2% | 1.90 | +7.2% |
| procene da, minus ne | 1083 | 55.6% | 1.96 | +7.8% |

## Sve kladionice, kola 8-14: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 6167 | 45.2% | 1.88 | -16.6% |
| minus-model okrenut, najjačih 30% ka preko | 1844 | 45.2% | 1.89 | -15.4% |
| procene, najjačih 30% ka preko | 1844 | 47.2% | 1.92 | -11.4% |
| oba se slažu za preko | 744 | 45.7% | 1.93 | -13.1% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 5-7: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 833 | 55.7% | 1.94 | +7.7% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 211 | 63.0% | 1.77 | +12.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 211 | 59.7% | 1.97 | +17.3% |
| novo: + 0,30·procene, po verovatnoći | 211 | 61.6% | 1.83 | +12.3% |
| **novo: + 0,30·procene, po vrednosti** | 211 | 59.2% | 2.00 | +18.0% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 8-14: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 1865 | 53.1% | 1.94 | +2.4% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 470 | 57.4% | 1.76 | +0.6% |
| ranije, po vrednosti (verovatnoća × kvota) | 470 | 54.7% | 1.98 | +7.8% |
| novo: + 0,30·procene, po verovatnoći | 470 | 57.9% | 1.80 | +4.0% |
| **novo: + 0,30·procene, po vrednosti** | 470 | 55.5% | 2.01 | +10.6% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-14

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 570 | 59.1% | 1.86 | +9.8% |
| **minus-model se slaže (msig ≥ 0.35)** | 317 | 59.6% | 1.85 | +9.8% |
| izbačeni (minus-model se ne slaže) | 253 | 58.5% | 1.88 | +9.7% |

