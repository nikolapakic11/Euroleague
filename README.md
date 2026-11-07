# Euroleague

Privatni repozitorijum sa dva odvojena projekta i jednom zajedničkom bazom javnih podataka.

## Struktura

| Folder | Šta je u njemu |
|---|---|
| `baza/` | Javni podaci koje koriste oba projekta: zapisnici utakmica Evrolige, raspored, statistika po igraču i utakmici, odbrana protivnika i tempo, snimci ponuda kladionica (Admiral, MaxBet, Soccerbet). |
| `minusi/` | Moja igra: aplikacija „Evroliga minusi“ (izvorni kod i rezervna kopija podataka), pomoćnici za Admiral i MaxBet, model za minuse, slaganje tiketa, planovi, praćenje uživo, analize. |
| `procene/` | Procene igrača sa rasponom, verovatnoće za preko i ispod na svakoj granici, poređenje granica i kvota više kladionica, javni sajt. |
| `spoj/` | Zajednički deo oba modela (od 7.11.2026): minus-model u Pythonu, signali za oba projekta, provera spoja posle svakog kola. |

## Pravilo odvajanja

Od 7.11.2026 (moja odluka): **logika modela** se deli u oba smera preko `spoj/` (minus-model pomaže procenama, model procena pomaže minusima), jer provera pokazuje da je spoj bolji od svakog modela posebno (`spoj/provera/izvestaj.md`).

I dalje važi: u `procene/` i na javni sajt ne idu moji tiketi, rezultati tiketa, ulozi ni pravila povraćaja.

## Važno

- Repozitorijum je privatan.
- Ovde ne idu podaci o nalozima na kladionicama (prijave, tokeni, lični podaci).
- Aplikacija „Evroliga minusi“ živi kao artefakt na claude.ai; `minusi/aplikacija/evroliga-minusi.html` i `stanje.json` su rezervna kopija od dana poslednjeg ažuriranja.
