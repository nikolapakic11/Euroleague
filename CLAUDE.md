# Uputstvo za Claude

Korisnik je Nikola. Piše na srpskom i očekuje odgovore na srpskom (latinica).

## Dva projekta, jedna baza, jedan razgovor (od 7.11.2026)

- `baza/`: javni podaci (zapisnici, raspored, statistika, ponude kladionica). Koriste je oba projekta.
- `minusi/`: Nikolina lična igra (minusi na igrače Evrolige, AdmiralBet, MaxBet kao rezerva). Privatno.
- `procene/`: procene igrača, poređenje kladionica i javni sajt.
- `spoj/`: zajednički deo oba modela (minus-model u Pythonu, signali, provera). Vidi `spoj/README.md`.
- Od 7.11.2026 oba projekta se vode u **jednom razgovoru** i koriste oba modela (odluka Nikole). Logika modela sme u oba smera (preko `spoj/`). Nikolini tiketi, rezultati tiketa, ulozi i pravila povraćaja ostaju samo u `minusi/` i nikad ne idu u `procene/` ni na javni sajt.

## Baza

- Zapisnik: `https://live.euroleague.net/api/Boxscore?gamecode=N&seasoncode=E2026` (curl sa `-H "User-Agent: curl/8.5.0"`), čuva se kao `baza/zapisnici/N.json`.
- Raspored: `https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games` → `baza/games.json`.
- `baza/skripte/build.py` pravi `rows.json` (igrač po utakmici), `ctx2.py <izlaz>` pravi kontekst (odbrana po poziciji `of`, tempo `lgp`/`tm`, igrači `pl`, dozvoljeno po timu `ta`).
- Ponude: `baza/ponude/<kladionica>/<datum>_<snimak>.json`. Soccerbet je dostupan direktno (`https://www.soccerbet.rs/restapi/offer/sr/...`, odgovor je gzip); igrači Evrolige su liga „Evroliga Igrači“ u sportu B, kače se na dan utakmice. Admiral i MaxBet dolaze preko pomoćnika (bookmarklet) koje Nikola pokreće; Mozzart i MaxBet nisu dostupni iz radnog okruženja (403).

## Rad u jednom razgovoru

- Ranije su minusi i procene rađeni u dva razgovora; od 7.11.2026 sve ide kroz jedan. Na početku rada `git pull`.
- Posle svakog kola: `baza/` (zapisnici, raspored, rows, ctx2, ponude), pa `minusi/` i `procene/`, pa `python3 spoj/provera.py` (provera spoja na novim ishodima).
- Dnevni tok za minuse: `minusi/optimizer/TOK.md`. Za procene: `procene/RAD.md`.
- Pre svakog slanja: `git pull --rebase`, pa `git push`.

## Minusi

- Aplikacija je artefakt na claude.ai (`https://claude.ai/artifact/AgLfxisKjdPWbAZM1Dr5cL`). Stanje je JSON u `<script type="application/json" id="state">`, kod u `<script id="app">` (izvor `minusi/aplikacija/app.js`).
- Stalna pravila igre (najmanja kvota 1,65, jedan igrač jedna stavka u listama, ponavljanje igrača do oko 30% tiketa, povraćaji, bonusi, dozvoljeni skokovi i asistencije protivnika) zapisana su u beleškama u stanju aplikacije (`notes`).
- Oznaka „Treba za nulu“ je namerno uklonjena iz aplikacije; ne vraćati je.
