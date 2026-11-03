# Uputstvo za Claude

Korisnik je Nikola. Piše na srpskom i očekuje odgovore na srpskom (latinica).

## Dva projekta, jedna baza

- `baza/`: javni podaci (zapisnici, raspored, statistika, ponude kladionica). Koriste je oba projekta.
- `minusi/`: Nikolina lična igra (minusi na igrače Evrolige, AdmiralBet, MaxBet kao rezerva). Privatno.
- `procene/`: novi projekat, procene igrača i poređenje kladionica. Ne sme da koristi ništa iz `minusi/` (tikete, rezultate tiketa, slaganje, pravila povraćaja, podešavanja modela). Podaci teku samo `baza/ → minusi/` i `baza/ → procene/`.

## Baza

- Zapisnik: `https://live.euroleague.net/api/Boxscore?gamecode=N&seasoncode=E2026` (curl sa `-H "User-Agent: curl/8.5.0"`), čuva se kao `baza/zapisnici/N.json`.
- Raspored: `https://api-live.euroleague.net/v2/competitions/E/seasons/E2026/games` → `baza/games.json`.
- `baza/skripte/build.py` pravi `rows.json` (igrač po utakmici), `ctx2.py <izlaz>` pravi kontekst (odbrana po poziciji `of`, tempo `lgp`/`tm`, igrači `pl`, dozvoljeno po timu `ta`).
- Ponude: `baza/ponude/<kladionica>/<datum>_<snimak>.json`. Soccerbet je dostupan direktno (`https://www.soccerbet.rs/restapi/offer/sr/...`, odgovor je gzip); igrači Evrolige su liga „Evroliga Igrači“ u sportu B, kače se na dan utakmice. Admiral i MaxBet dolaze preko pomoćnika (bookmarklet) koje Nikola pokreće; Mozzart i MaxBet nisu dostupni iz radnog okruženja (403).

## Rad u dva razgovora

- Minusi se rade u jednom razgovoru, procene u drugom. Oba rade na ovom repozitorijumu.
- Razgovor za minuse posle svakog kola ažurira `baza/` (zapisnici, raspored, rows, ctx2, Admiral ponude) i `minusi/`, pa šalje na GitHub.
- Razgovor za procene na početku rada uradi `git pull`, čita `baza/`, a piše samo u `procene/` i u `baza/ponude/mozzart/` i `baza/ponude/soccerbet/`. Ne menja ostatak `baza/` i nikad ne dira `minusi/`.
- Pre svakog slanja: `git pull --rebase`, pa `git push`.

## Minusi

- Aplikacija je artefakt na claude.ai (`https://claude.ai/artifact/AgLfxisKjdPWbAZM1Dr5cL`). Stanje je JSON u `<script type="application/json" id="state">`, kod u `<script id="app">` (izvor `minusi/aplikacija/app.js`).
- Stalna pravila igre (najmanja kvota 1,65, jedan igrač jedna stavka u listama, ponavljanje igrača do oko 30% tiketa, povraćaji, bonusi, dozvoljeni skokovi i asistencije protivnika) zapisana su u beleškama u stanju aplikacije (`notes`).
- Oznaka „Treba za nulu“ je namerno uklonjena iz aplikacije; ne vraćati je.
