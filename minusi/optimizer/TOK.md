# Dnevni tok za minuse (Admiral)

Sve skripte se pokreću sa `python3 -I`, putanje se računaju od korena repozitorijuma (`minusi/putanje.py`).

1. **Podaci posle kola:** `python3 baza/skripte/build.py` → `baza/rows.json`, pa `python3 baza/skripte/ctx2.py baza/ctx2.json`.
2. **Ponuda u aplikaciju:** `python3 minusi/optimizer/load.py <nova_app.html> baza/ponude/admiral/<datum>_<x>.json [--kvote kvote.json] [--povrede povrede.json]`.
   Polazi od `minusi/aplikacija/evroliga-minusi.html` i snima novu kopiju; bez `--kvote` i `--povrede` ostaju postojeće u stanju.
3. **Kandidati iz Generatora:** `python3 minusi/optimizer/scrape.py <nova_app.html> <pool.json> "" ""`.
4. **Ulaz za optimizer:** `python3 minusi/optimizer/izbor.py <pool.json> <ponuda.json> <sel.json> --najmanja 1.65`.
5. **Tiketi:** `python3 minusi/optimizer/optg7.py '<cfg JSON>'` (primeri cfg u `minusi/arhiva/kola/r9/`; ključevi `sizes`, `gcaps`, `tcap`, `maxu`, `pmax`, `lowu`, `lowmax`).
