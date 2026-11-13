# Dnevni tok za minuse (Admiral)

Sve skripte se pokreću sa `python3 -I`, putanje se računaju od korena repozitorijuma (`minusi/putanje.py`).

1. **Podaci posle kola:** `python3 baza/skripte/build.py` → `baza/rows.json`, pa `python3 baza/skripte/ctx2.py baza/ctx2.json`.
2. **Ponuda u aplikaciju:** `python3 minusi/optimizer/load.py <nova_app.html> baza/ponude/admiral/<datum>_<x>.json [--kvote kvote.json] [--povrede povrede.json]`.
   Polazi od `minusi/aplikacija/evroliga-minusi.html` i snima novu kopiju; bez `--kvote` i `--povrede` ostaju postojeće u stanju.
3. **Kandidati iz Generatora:** `python3 minusi/optimizer/scrape.py <nova_app.html> <pool.json> "" ""`.
4. **Ulaz za optimizer:** `python3 minusi/optimizer/izbor.py <pool.json> <ponuda.json> <sel.json> --najmanja 1.60`.
   Od 7.11.2026 verovatnoća `pr` = tržište + 0,15·minus (aplikacija) + 0,30·model procena (`spoj/signali.py`); stara je u `pr_staro`
   (`--bez-procena` vraća staro). Pre ovoga osvežiti `baza/rows.json` (procene računaju iz utakmica pre dana).
5. **Tiketi:** `python3 minusi/optimizer/optg7.py '<cfg JSON>'` (primeri cfg u `minusi/arhiva/kola/r10d3/`; ključevi `sizes`, `gcaps`, `tcap`, `maxu`, `pmax`, `lowu`, `lowmax`, `lowothers`, **`kv`**).

## Spoj sa procenama i isplata (od 7.11.2026)
- U cfg staviti `"kv": 1`: dobitni tiket se broji po isplati (proizvod kvota), ne samo po broju dobitnih. Bez toga optimizer bira najniže kvote, a one ne prolaze češće nego što kvota kaže.
- Provera (`spoj/provera/izvestaj.md`, kola 8–10, Admiral, najboljih 25% dana): staro 53,3% prolaza, kvota 1,78, povraćaj −5,6%; novo (procene + izbor po vrednosti) 56,1%, kvota 2,01, +12,3%. Simulacija planova za 6 dana (260 tiketa): parovi 53,6% → 53,8%, prosečna kvota para 1,86 → 1,96.
- Ispis optimizera sada ima i `isplata` (očekivani povraćaj po ulogu, 1,0 = nula; bez povraćaja i bonusa).
- Ponoviti `python3 spoj/provera.py` posle svakog kola; ako spoj prestane da pomaže, vratiti `kv: 0` i `--bez-procena`.

## Stalno pravilo: ograničeno ponavljanje (od 6.11.2026)
Nikola je odredio da se ponavljanje ograničava čak i po cenu slabijih parova: jedan igrač (stavka) ne sme na više od ~15% tiketa plana.
U optg7 cfg: `maxu = pmax = ceil(0.15 * broj_tiketa)` (40 tiketa → 6; 30 → 5; 20 → 3), `tcap` 2, `gcaps` 3 za osmice i 4 za desetke.
Razlog: 6.11. su Brown, Hoard, Pajola (po 10 tiketa) i Wright IV, Kabengele, Diarra (po 9) srušili 35 od 40 tiketa, iako je cela ponuda pogodila 58,5%.
Test na istoj ponudi: ograničenje 10 → 6 smanjuje očekivani broj dobitnih tiketa za ~8% (0,189 → 0,174, model), a deljenje igrača među tiketima pada sa 19% na 12%. Zato se isplati.

## Novi parametri i pravila izbora (od 12.11.2026; analiza `spoj/analiza/IZVESTAJ_2026-11-12.md`)
- `izbor.py` sada računa `pr` naučenim spojem (`signali.spoj2`, težine `spoj/tezine.json`): tržište + oba modela + izostanci u timu
  + granica prema proseku igrača + kazna za poene 7,5–10,5. Stari spoj je u `pr1`.
- Filteri: tim kome fali 35+ minuta rotacije (izveštaj o povredama `procene/podaci/povrede.json`, `--van`/`--igra` za vesti dana),
  osim poena 3–5. strelca; `--ranija <ponuda>` izbacuje minuse kojima je granica podignuta od ranijeg snimka.
- Bazen: `--vrh 0.38` (nivo A = oba modela u najjačih 30% dana, plus najboljih 38% po vrednosti). Manji bazen znači više ponavljanja:
  za tikete od 8 parova i ponavljanje do 20% treba oko 40 parova; desetke i dvanaestice traže više.
- Posle svakog kola: `python3 spoj/provera.py && python3 spoj/analiza/prep.py && python3 spoj/tezine.py` (nove težine).
- Dužine: osnova su osmice; desetke i dvanaestice samo po Nikolinoj želji, po 50 din, iz istog bazena.

## Hibrid raspored (osnova od 12.11.2026, odluka Nikole)
- `optg7.py` ključ `"jezgro"` (podrazumevano trećina tiketa, najkraći): ti tiketi smeju samo najjače parove (nivo A + najboljih
  `"jtop"` po vrednosti, podrazumevano četvrtina bazena); ostali tiketi su mešani. `"jezgro": 0` vraća stari raspored.
- Provera unazad (`spoj/analiza/raspored.py`, 16 odigranih dana, isti parovi, samo drugi raspored): isplata/ulog 1,78 (hibrid)
  prema 1,12 (raspršeno) i 1,45 (čisti slojevi); prednost dolazi iz 3 dana, ređi dobitni dani. Pratiti 2–3 kola.

## Od 13.11.2026

- `pr` u `izbor.py` (spoj2) ima i trend minuta, formu, tempo i kolebanje minuta (mali dobitak) i dodatak kad je granica
  spuštena od ranijeg snimka (`--ranija`; polje `spustena`). Posle kola: `provera.py`, `analiza/prep.py`, `tezine.py`.
- Nalaz za tikete (nije primenjeno, odluka Nikole): skokovi ispod koje spoj najviše ceni ne prolaze češće od ostalih;
  asistencije ispod su najjače. Po verovatnoći (ne po vrednosti) vrh prolazi ~68% uz kvotu ~1,80.

- Svako jutro posle dana sa utakmicama: `python3 spoj/posle_kola.py` (zapisnici, baza, ponovno učenje spoja, provera pravila, učinak sajta). `load.py` sada sam osvežava statistiku timova, raspored i povrede u aplikaciji.
