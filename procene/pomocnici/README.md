# Pomoćnici

## Mozzart (`mozzart.js`)

Mozzart nije dostupan iz radnog okruženja (403), pa ponudu hvata pomoćnik u tvom pregledaču.

Postavljanje (jednom):
1. Napravi novi obeleživač (bookmark) bilo koje stranice.
2. Izmeni ga: naziv „Mozzart pomoćnik“, a u polje za adresu nalepi ceo sadržaj fajla `mozzart_bookmarklet.txt` (počinje sa `javascript:`).

Upotreba:
1. Otvori mozzartbet.com, idi na Košarka, Evroliga, ponuda igrača.
2. Klikni obeleživač. Dole desno se pojavi panel.
3. Proklikni utakmice ili igrače da stranica učita ponudu (panel broji uhvaćene odgovore, granice i igrače).
4. „Izvezi“ preuzima `<datum>_mozzart_<vreme>.json` u formatu v2.
5. Okači fajl na GitHub u `baza/ponude/mozzart/` (u aplikaciji ili na sajtu: Add file → Upload files), ili ga pošalji u razgovor za procene. Sledeće zakazano pokretanje ga uzima automatski.

Isto važi za Admiral i MaxBet: fajl iz njihovih pomoćnika ide u `baza/ponude/admiral/` odnosno `baza/ponude/maxbet/`; ime može biti bilo koje dok sadrži datum (npr. `2026-11-04_a.json`).

Ako panel pokazuje 0 granica iako je ponuda otvorena: klikni „Sirovo“ i pošalji taj fajl. Na osnovu njega se čitač prilagodi tačnom Mozzartovom formatu. Prva verzija čitača je napravljena bez pristupa Mozzartu, pa je prvi pravi snimak ujedno i provera.

Pomoćnik ne hvata ništa vezano za nalog (prijava, stanje, tiketi, lični podaci se preskaču i brišu iz uhvaćenog).

Ponovna izrada `mozzart_bookmarklet.txt` posle izmene `mozzart.js`: terser, pa `javascript:` + encodeURIComponent(kod).

## Soccerbet

Nema pomoćnika, preuzima se direktno: `python3 procene/skripte/soccerbet.py` (vidi opis u skripti).
