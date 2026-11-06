# Izvori: koji sajtovi rade iz radnog okruženja (stanje 6.11.2026)

Nikola traži (6.11.2026): pri analizi i pravljenju predloga otvarati razne sajtove (vesti, povrede, sastavi, kvote,
statistika), ne samo podatke iz repozitorijuma. Proveriti povrede i vesti pre svakih predloga za dan.

Provera iz komandne linije (pristup početnoj stranici; pojedine stranice mogu da se ponašaju drugačije).

## Rade

- Evroliga, rezultati i raspored: `live.euroleague.net`, `api-live.euroleague.net`
- Vesti i povrede: `eurohoops.net` (stranica `/en/euroleague/`), `basketnews.com`, `eurodevotion.com`
- Kladionice: `admiralbet.rs`, `maxbet.rs`, `soccerbet.rs`
- Statistika i kvote: `flashscore.com`, `oddsportal.com`, `sportsgambler.com`, `rotowire.com`, `basketball-reference.com`, `espn.com`
- Pretraživači: `google.com`, `bing.com`, `duckduckgo.com`
- Srpske vesti: `mondo.rs`, `b92.net`
- GitHub API: `api.github.com`

## Rade sa ograničenjem

- `euroleaguebasketball.net`: iz komandne linije 429 (previše zahteva), ali alat za čitanje stranica (WebFetch) radi i čita izveštaj o povredama.
- `feeds.incrowdsports.com`: početna stranica 502; aplikacija ga koristi za prosečnu statistiku, treba proveriti tačne adrese.
- `github.com` i `raw.githubusercontent.com`: početna stranica 400, ali `git push` i `pull` rade.

## Ne rade

- Traže da ih botovi ne otvaraju (403): `mozzartbet.com`, `meridianbet.rs`, `sofascore.com`, `realgm.com`, `proballers.com`.
  Mozzart se čita preko Chrome-a (`procene/alati/mozzart_citac.js`).
- Nedostupni: `basketballsphere.com`, `kosarka.rs`

## Napomene

- Eurohoops i BasketNews preusmeravaju posetioca: čitati ih sa nastavkom putanje (npr. `https://www.eurohoops.net/en/euroleague/`,
  `https://basketnews.com/leagues/25-euroleague/injured.html`), a alatu za čitanje stranica davati već preusmerenu adresu.
- Ova sesija 6.11.: `povrede.py` je ujutru dobio 403 od Eurohoopsa, a u 11h radi (Eurohoops i BasketNews, 76 igrača).
  Ako opet odbije, ponoviti kasnije ili pročitati izveštaj alatom za čitanje stranica i upisati u `procene/podaci/povrede_rucno.json`.
- Isti spisak važi i za razgovor o minusima.
