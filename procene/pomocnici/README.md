# Pomoćnici

## Mozzart (`mozzart.js`)

Mozzart nije dostupan iz radnog okruženja (403), pa ponudu hvata pomoćnik u tvom pregledaču.

Postavljanje (jednom):
1. Napravi novi obeleživač (bookmark) bilo koje stranice.
2. Izmeni ga: naziv „Mozzart pomoćnik“, a u polje za adresu nalepi ceo sadržaj fajla `mozzart_bookmarklet.txt` (počinje sa `javascript:`).

Upotreba:
1. Otvori mozzartbet.com → Klađenje → u levoj traci „Izdvojena ponuda“ → Igrači (bilo koje takmičenje).
2. Klikni obeleživač. Dole desno se pojavi panel i sam preuzme ponudu igrača za sva košarkaška takmičenja iz „Igrači“ (traje par sekundi).
3. Panel pokaže broj granica, igrača i utakmica po takmičenju.
4. „Izvezi“ preuzima `<datum>_mozzart_<vreme>.json` u formatu v2.
5. Okači fajl na GitHub u `baza/ponude/mozzart/` (u aplikaciji ili na sajtu: Add file → Upload files), ili ga pošalji u razgovor za procene. Sledeće zakazano pokretanje ga uzima automatski.

Isto važi za Admiral i MaxBet: fajl iz njihovih pomoćnika ide u `baza/ponude/admiral/` odnosno `baza/ponude/maxbet/`; ime može biti bilo koje dok sadrži datum (npr. `2026-11-04_a.json`).

Provereno 3.11.2026 na pravoj ponudi (Evrokup, Liga šampiona, Francuska, Nemačka: 61 granica). Mozzart igru zove npr. „Broj poena E.Tubutis“ (inicijal i prezime) i ne navodi tim, samo utakmicu, pa skripte igrača traže među igračima ta dva tima. Tada je u ponudi „Igrači“ bilo samo poena; skokovi i asistencije se prepoznaju istim čitačem ako ih bude. Ako panel pokaže 0 granica iako ponuda postoji, klikni „Sirovo“ i pošalji taj fajl.

Pomoćnik ne hvata ništa vezano za nalog (prijava, stanje, tiketi, lični podaci se preskaču i brišu iz uhvaćenog).

Ponovna izrada `mozzart_bookmarklet.txt` posle izmene `mozzart.js`: terser, pa `javascript:` + encodeURIComponent(kod).

## Soccerbet

Nema pomoćnika, preuzima se direktno: `python3 procene/skripte/soccerbet.py` (vidi opis u skripti).
