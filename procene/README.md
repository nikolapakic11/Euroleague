# Procene

Procene igrača Evrolige zasnovane na statistici i kontekstu, bez tipova i bez tiketa.

## Šta treba da daje

- Za svakog igrača i stavku (poeni, skokovi, asistencije): očekivani učinak i raspon.
- Verovatnoću za preko i ispod na bilo kojoj granici, za svaku kladionicu posebno.
- Granice i kvote Admirala, MaxBeta, Mozzarta i Soccerbeta jednu pored druge, najbolju cenu i slučajeve kad se granice razilaze toliko da mogu da prođu i preko i ispod.
- Kontekst: protivnik (odbrana po poziciji, dozvoljeni skokovi i asistencije), tempo, očekivani minuti, povrede i ko dobija minute, forma.
- Dnevnik svake procene sa ishodom, za proveru tačnosti u oba smera.

## Plan

1. Model raspona (umesto „da li minus prolazi“) i provera na ponudama od oktobra, za pluseve i minuse.
2. Preuzimanje ponuda: Soccerbet direktno, Admiral i MaxBet preko postojećih pomoćnika, Mozzart novi pomoćnik.
3. Probna tabla za kolo 11 (11. do 13.11.2026) i dnevnik procena od tog kola.
4. Javna stranica sa predlozima po kolu od kola 11 (odluka 3.11.2026), sa svim ishodima.

U pozadini (odluka 4.11.2026): prikupljaju se domaće utakmice ekipa između kola Evrolige i minuti igrača u njima (`domace.py`). Posle nekoliko kola proveriti obrazac: da li domaća utakmica dan ili dva pre kola, ili mnogo minuta u njoj, menja minute i učinak u Evroligi, i da li to vredi uneti u model. Do tada se ništa od toga ne prikazuje.

Ovaj folder koristi samo `baza/`. Ništa iz `minusi/`.

## Kako se radi

Sve skripte se pokreću iz korena repozitorijuma. Ceo dnevni posao radi jedna komanda:
`python3 procene/skripte/dan.py` (ujutru sa `--jutro`). Nju pokreću zakazani zadaci (Ut–Pet), pa šalju na GitHub i objavljuju obe stranice.

| Korak | Komanda | Šta radi |
|---|---|---|
| Soccerbet ponuda | `python3 procene/skripte/soccerbet.py` | Snimak igrača Evrolige u `baza/ponude/soccerbet/<datum>_<slovo>.json` (format v2, sve granice, `m=1` je glavna). Pokreće se na dan utakmice. |
| Mozzart ponuda | pomoćnik u pregledaču | Vidi `procene/pomocnici/README.md`. Izvezeni fajl ide u `baza/ponude/mozzart/`. |
| Prošla sezona | `python3 procene/skripte/prosla_sezona.py <folder>` | Polazne procene igrača iz E2025 u `procene/podaci/e2025_igraci.json` (već urađeno). |
| Podešavanje modela | `python3 procene/skripte/podesi.py --do-kola 6` | Parametri u `procene/model_parametri.json`, podešeni na učinke, ne na ponude. |
| Provera | `python3 procene/skripte/provera.py` | `procene/provera/izvestaj.md`: model naspram kvota na svim ponudama od oktobra, preko i ispod. |
| Tabla | `python3 procene/skripte/tabla.py --kolo 11 --dnevnik` | `procene/tabla/kolo11.json` i `.html` (objavljuje se kao artefakt) i dnevnik procena. |
| Spajanje | `python3 procene/skripte/spajanje.py` | Posle provere: spaja model i kvote u jednu verovatnoću podešenu prema ishodima (`procene/spajanje.json`), sa testom na kolima 7 do 9. |
| Javni predlozi | `python3 procene/skripte/predlozi.py --kolo 11` | Posle table. 4 do 6 predloga po utakmici (izbor u tabli, `spajanje.izbor_utakmice`): rang po spojenoj verovatnoći, MINUS od 53%, PLUS od 50% (do 2 PLUS unapred), kvota ≥ 1,50, jedan po igraču; nivoi jak/solidan/nagoveštaj/slab; uz predlog opseg ponuđenih granica (i Soccerbet lestvice „N+“), soft spot i kratka analiza (minuti, sezona, forma, odbrana, tempo, igrači na poziciji, odsutni). Na javnu stranicu ne idu provera unazad ni pragovi po strani. Zaključava na početku utakmice, upisuje ishode, pravi `procene/javno/predlozi.html`. |
| Dopuna | `python3 procene/skripte/dopuna.py` | Završene utakmice koje još nisu u `baza/rows.json`, direktno iz Evrolige, u `procene/podaci/dopuna.json`. |
| Sastavi | `python3 procene/skripte/sastavi.py` | 12 prijavljenih igrača kad ih Evroliga objavi; ko nije u sastavu, ne igra. |
| Sajt | `python3 procene/skripte/sajt.py <folder>` | Javna stranica kao samostalan `index.html` za javni repozitorijum `nikolapakic11/evroliga-plus-minus` (GitHub Pages); u njega ide samo stranica. |
| Domaće utakmice | `python3 procene/skripte/domace.py` (`--pregled`) | U pozadini, bez prikaza: utakmice ekipa Evrolige u domaćim ligama i kupovima (Flashscore) sa minutima, poenima, skokovima i asistencijama igrača, i raspored narednih. `procene/podaci/domace/`. Pokreće se u jutarnjem radu. |
| Ishodi | `python3 procene/skripte/dnevnik.py --kolo 11` | Upisuje stvarne učinke u dnevnik i ispisuje tačnost. |

Minuti su prosek igrača u ovoj sezoni (fiksno). Izuzetak za povredu ili „ne igra“ samo kroz `procene/minuti.json`, npr. `{"11": {"nikola milutinov": 0}}` (ključ je ime malim slovima, bez kvačica).

Tabla (tekuće kolo, `procene/tabla/aktuelno.html`): https://claude.ai/artifact/P3awRXNbkBvDErZ8Jug9vZ
Javna stranica sa predlozima: https://claude.ai/artifact/HUT71aS4AnLVknR6pKgpDv (javna kad se uključi deljenje u meniju Share)

Model ukratko: prosek minuta u sezoni × učinak po minutu (ova sezona, skupljena ka prošloj sezoni, pa ka proseku pozicije) × odbrana protivnika prema poziciji × tempo; raspodela je negativna binomna. Detalji u `procene/skripte/model.py`.
