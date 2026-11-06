# Dnevni tok za minuse (Admiral)

Sve skripte se pokreću sa `python3 -I`, putanje se računaju od korena repozitorijuma (`minusi/putanje.py`).

1. **Podaci posle kola:** `python3 baza/skripte/build.py` → `baza/rows.json`, pa `python3 baza/skripte/ctx2.py baza/ctx2.json`.
2. **Ponuda u aplikaciju:** `python3 minusi/optimizer/load.py <nova_app.html> baza/ponude/admiral/<datum>_<x>.json [--kvote kvote.json] [--povrede povrede.json]`.
   Polazi od `minusi/aplikacija/evroliga-minusi.html` i snima novu kopiju; bez `--kvote` i `--povrede` ostaju postojeće u stanju.
3. **Kandidati iz Generatora:** `python3 minusi/optimizer/scrape.py <nova_app.html> <pool.json> "" ""`.
4. **Ulaz za optimizer:** `python3 minusi/optimizer/izbor.py <pool.json> <ponuda.json> <sel.json> --najmanja 1.65`.
5. **Tiketi:** `python3 minusi/optimizer/optg7.py '<cfg JSON>'` (primeri cfg u `minusi/arhiva/kola/r9/`; ključevi `sizes`, `gcaps`, `tcap`, `maxu`, `pmax`, `lowu`, `lowmax`).

## Stalno pravilo: ograničeno ponavljanje (od 6.11.2026)
Nikola je odredio da se ponavljanje ograničava čak i po cenu slabijih parova: jedan igrač (stavka) ne sme na više od ~15% tiketa plana.
U optg7 cfg: `maxu = pmax = ceil(0.15 * broj_tiketa)` (40 tiketa → 6; 30 → 5; 20 → 3), `tcap` 2, `gcaps` 3 za osmice i 4 za desetke.
Razlog: 6.11. su Brown, Hoard, Pajola (po 10 tiketa) i Wright IV, Kabengele, Diarra (po 9) srušili 35 od 40 tiketa, iako je cela ponuda pogodila 58,5%.
Test na istoj ponudi: ograničenje 10 → 6 smanjuje očekivani broj dobitnih tiketa za ~8% (0,189 → 0,174, model), a deljenje igrača među tiketima pada sa 19% na 12%. Zato se isplati.
