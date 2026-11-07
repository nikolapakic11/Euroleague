# Spoj: minus-model i model procena zajedno

Od 7.11.2026 oba projekta koriste oba modela (odluka Nikole: objediniti razgovore i izvući najbolje iz oba).
Svaki model ostaje kakav jeste. Spajaju se samo njihove procene, i to samo tamo gde je provera pokazala da to pomaže.

| Fajl | Šta radi |
|---|---|
| `minus_model.py` | Prepis funkcije `estimate()` iz aplikacije za minuse (Generator) u Pythonu. Računa samo iz utakmica pre dana. Bez dodatka za odsutne saigrače; polazna procena je prošla sezona (`procene/podaci/e2025_igraci.json`). Vernost: na kolima 4–7 najbolja četvrtina prolazi 68% (aplikacija beleži 69%). |
| `signali.py` | Zajednički ulaz: `Signali().procene_preko(...)` (model procena), `Signali().minus(...)` (minus-model) i `spoj_ispod(...)` (verovatnoća ispod za tikete). |
| `provera.py` | Ponovljiva provera na svim ponudama (`python3 spoj/provera.py`). Izlaz je `spoj/provera/izvestaj.md`. Ponoviti posle svakog kola. |
| `dnevnik/` | MINUS kandidati za sajt koje je izbacio minus-model (`izbaceni_<dan>.json`), za kasniju proveru. |

## Šta je uključeno

1. **Procene (sajt):** MINUS predlog ulazi samo kad se i minus-model slaže, to jest kad je `msig` (deo minus-procene koji ne dolazi iz kvota) bar 0,35 (medijana).
   - Kola 5–7: kandidati sa kojima se slaže prolazili su 64%, izbačeni 52%.
   - Kola 8–10: 62,5% naspram 53%.
   - Minus-model posebno ispravlja igrače bez prošle sezone u Evroligi, gde model procena greši.

   Kod je u `procene/skripte/predlozi.py` (`DAN_MINUS_SLAGANJE`). Ručno dodati predlozi ne zavise od ovog uslova.
2. **Minusi (tiketi):** u verovatnoću za tikete (`minusi/optimizer/izbor.py`) ulazi i model procena: tržište + 0,15·minus + 0,30·procene.
   - Optimizer ima novu opciju `kv` (`minusi/optimizer/optg7.py`). Sa `kv: 1` dobitni tiket se broji po isplati, a ne samo po broju.
   - Kola 8–10, najboljih 25% dana: ranije 53% prolaza uz kvotu 1,78 (povraćaj −6%), sada 56% uz kvotu 2,01 (+12%).
   - Simulacija plana tiketa (6 dana, 260 tiketa): isti procenat prolaza parova (54%), ali prosečna kvota para 1,96 umesto 1,86.

## Šta nije uključeno (provera ne pokazuje korist)

- **Minus-model okrenut za PLUS:** njegovih najjačih 30% ka preko prolazi kao i bez modela (47%).
- **Bilo koji spoj za PLUS:** tržište sistematski precenjuje preko. Kvote kažu oko 51%, a prolazi 45–48%. Nijedan model ne nalazi pluseve koji se isplate.
- **Naučene (regresijske) težine po kolu:** težina minus-modela pada iz kola u kolo (0,75 → 0,46), jer je on podešen na kolima 4–7. Zato su težine fiksne i umerene.

## Pravilo odvajanja (novo)

- **Logika modela** sme da ide u oba smera (`minusi/` ↔ `procene/`, preko `spoj/`).
- **Nikolini tiketi, rezultati tiketa, ulozi i pravila povraćaja** ostaju samo u `minusi/` i nikad ne idu na javni sajt.
