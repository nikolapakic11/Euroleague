# Kladionice: tačnost, razlike granica, kretanje kvota

Zapisa sa ishodom: 978. Uzorak sa više kladionica je mali (od 4.11.2026); izveštaj se osvežava sa svakim danom.

## 1. Svaka kladionica na svojim granicama (poslednji snimak dana)

| kladionica | granica | marža | log gubitak | stvarno preko | fer preko |
|---|---|---|---|---|---|
| admiral | 795 | 6.5% | 0.6898 | 48.7% | 50.5% |
| maxbet | 364 | 7.1% | 0.6803 | 50.0% | 50.6% |
| mozzart | 156 | 6.8% | 0.6798 | 50.6% | 50.3% |
| soccerbet | 183 | 7.1% | 0.6797 | 51.4% | 50.5% |

## 2. Parovi na istoj granici (ista igrač, stavka, dan, granica): čija fer verovatnoća je tačnija

| par | granica | log gubitak A | log gubitak B |
|---|---|---|---|
| admiral – maxbet | 173 | 0.6835 | 0.6793 |
| admiral – mozzart | 129 | 0.6826 | 0.6789 |
| admiral – soccerbet | 169 | 0.6824 | 0.6796 |
| maxbet – mozzart | 131 | 0.6787 | 0.6801 |
| maxbet – soccerbet | 174 | 0.6796 | 0.6806 |
| mozzart – soccerbet | 132 | 0.6779 | 0.6778 |

## 3. Kad se granice razlikuju (33 slučajeva)

- PREKO na najnižoj granici: prošlo 20/33, povraćaj +8.0%
- ISPOD na najvišoj granici: prošlo 14/33, povraćaj -21.2%
- Najniža granica najčešće kod: {'soccerbet': 11, 'mozzart': 25, 'admiral': 5, 'maxbet': 8}; najviša: {'admiral': 28, 'maxbet': 24, 'mozzart': 5, 'soccerbet': 22}
  - admiral sam ima najnižu granicu: 1, preko prošlo 0
  - admiral sam ima najvišu granicu: 4, ispod prošlo 3
  - maxbet sam ima najnižu granicu: 1, preko prošlo 1
  - maxbet sam ima najvišu granicu: 1, ispod prošlo 0
  - mozzart sam ima najnižu granicu: 18, preko prošlo 11
  - mozzart sam ima najvišu granicu: 1, ispod prošlo 0
  - soccerbet sam ima najnižu granicu: 2, preko prošlo 1
  - soccerbet sam ima najvišu granicu: 2, ispod prošlo 1

## 4. Kretanje u toku dana, prvi → poslednji snimak (74 pomeranja)

„gore“ = granica porasla ili verovatnoća za preko porasla. Pitanje: da li ishod ide u smeru pomeranja.

- granica gore: 33, ishod u smeru pomeranja 17/33 (52%)
- granica dole: 19, ishod u smeru pomeranja 15/19 (79%)
- kvota gore: 13, ishod u smeru pomeranja 6/13 (46%)
- kvota dole: 9, ishod u smeru pomeranja 4/9 (44%)
  - admiral: 38 pomeranja, u smeru 20
  - maxbet: 15 pomeranja, u smeru 10
  - mozzart: 5 pomeranja, u smeru 4
  - soccerbet: 16 pomeranja, u smeru 8
