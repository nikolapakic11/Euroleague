# Spoj minus-modela i modela procena: provera

Granica sa ishodom: 3182 (admiral, maxbet, mozzart, soccerbet), kola 4-10. Čist test (posle podešavanja minus-modela): kola 8-10. Rang se računa unutar dana.

## Admiral, kola 8-10: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 902 | 52.1% | 1.92 | -0.7% |
| samo minus-model, najjačih 30% dana | 274 | 53.3% | 1.93 | +2.1% |
| samo procene, najjačih 30% dana | 274 | 56.2% | 1.97 | +10.5% |
| **oba se slažu (oba u najjačih 30%)** | 122 | 60.7% | 1.98 | +19.2% |
| minus da, procene ne | 152 | 47.4% | 1.89 | -11.6% |
| procene da, minus ne | 152 | 52.6% | 1.95 | +3.5% |

## Admiral, kola 8-10: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 902 | 47.9% | 1.88 | -10.9% |
| minus-model okrenut, najjačih 30% ka preko | 267 | 46.8% | 1.90 | -11.3% |
| procene, najjačih 30% ka preko | 267 | 49.4% | 1.92 | -7.4% |
| oba se slažu za preko | 103 | 47.6% | 1.93 | -8.6% |

## Sve kladionice, kola 8-10: ISPOD

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek ispod | 1880 | 52.4% | 1.92 | -0.3% |
| samo minus-model, najjačih 30% dana | 569 | 56.2% | 1.93 | +7.5% |
| samo procene, najjačih 30% dana | 569 | 56.2% | 1.97 | +10.9% |
| **oba se slažu (oba u najjačih 30%)** | 252 | 63.1% | 1.98 | +24.0% |
| minus da, procene ne | 317 | 50.8% | 1.88 | -5.7% |
| procene da, minus ne | 317 | 50.8% | 1.96 | +0.4% |

## Sve kladionice, kola 8-10: PREKO

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| uvek preko | 1880 | 47.6% | 1.87 | -12.0% |
| minus-model okrenut, najjačih 30% ka preko | 562 | 47.7% | 1.90 | -10.1% |
| procene, najjačih 30% ka preko | 562 | 51.1% | 1.91 | -4.8% |
| oba se slažu za preko | 231 | 47.6% | 1.94 | -9.1% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 5-7: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 833 | 55.7% | 1.94 | +7.7% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 211 | 63.0% | 1.77 | +12.2% |
| ranije, po vrednosti (verovatnoća × kvota) | 211 | 59.7% | 1.97 | +17.3% |
| novo: + 0,30·procene, po verovatnoći | 211 | 61.6% | 1.83 | +12.3% |
| **novo: + 0,30·procene, po vrednosti** | 211 | 59.2% | 2.00 | +18.0% |

## Minusi (Admiral, kvota ispod ≥ 1,60), kola 8-10: najboljih 25% dana

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| sve | 853 | 51.3% | 1.95 | -0.6% |
| ranije: po verovatnoći (tržište + 0,15·minus) | 214 | 53.3% | 1.78 | -5.6% |
| ranije, po vrednosti (verovatnoća × kvota) | 214 | 52.3% | 1.97 | +2.8% |
| novo: + 0,30·procene, po verovatnoći | 214 | 52.8% | 1.82 | -3.8% |
| **novo: + 0,30·procene, po vrednosti** | 214 | 56.1% | 2.01 | +12.3% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 5-7

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 670 | 57.8% | 1.90 | +9.6% |
| **minus-model se slaže (msig ≥ 0.35)** | 321 | 63.9% | 1.89 | +20.2% |
| izbačeni (minus-model se ne slaže) | 349 | 52.1% | 1.91 | -0.1% |

## Procene (sajt): MINUS kandidati po pravilu (prednost ≥ 6%, ≥ 54%), kola 8-10

| izbor | granica | prošlo | prosečna kvota | povraćaj na ulog |
|---|---|---|---|---|
| svi kandidati | 139 | 59.0% | 1.88 | +11.1% |
| **minus-model se slaže (msig ≥ 0.35)** | 88 | 62.5% | 1.88 | +17.0% |
| izbačeni (minus-model se ne slaže) | 51 | 52.9% | 1.89 | +0.9% |

