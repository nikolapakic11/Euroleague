# Euroleague

Privatni repozitorijum sa dva odvojena projekta i jednom zajedničkom bazom javnih podataka.

## Struktura

| Folder | Šta je u njemu |
|---|---|
| `baza/` | Javni podaci koje koriste oba projekta: zapisnici utakmica Evrolige, raspored, statistika po igraču i utakmici, odbrana protivnika i tempo, snimci ponuda kladionica (Admiral, MaxBet, Soccerbet). |
| `minusi/` | Moja igra: aplikacija „Evroliga minusi“ (izvorni kod i rezervna kopija podataka), pomoćnici za Admiral i MaxBet, model za minuse, slaganje tiketa, planovi, praćenje uživo, analize. |
| `procene/` | Novi projekat: procene igrača sa rasponom, verovatnoće za preko i ispod na svakoj granici, poređenje granica i kvota više kladionica. |

## Pravilo odvajanja

Podaci teku samo u jednom smeru:

- `baza/` → `minusi/`
- `baza/` → `procene/`
- **nikad** `minusi/` → `procene/`

U `procene/` ne ide ništa iz `minusi/`: ni tiketi, ni rezultati tiketa, ni način slaganja, ni pravila povraćaja, ni podešavanja modela nastala na mojim minusima. Ako se nešto iz `procene/` pokaže korisnim, ja odlučujem da li to preuzimam u `minusi/`.

## Važno

- Repozitorijum je privatan.
- Ovde ne idu podaci o nalozima na kladionicama (prijave, tokeni, lični podaci).
- Aplikacija „Evroliga minusi“ živi kao artefakt na claude.ai; `minusi/aplikacija/evroliga-minusi.html` i `stanje.json` su rezervna kopija od dana poslednjeg ažuriranja.
