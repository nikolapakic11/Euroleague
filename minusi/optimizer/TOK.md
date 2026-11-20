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

## Hibrid raspored (od 12.11.2026; od 14.11. ZAMENJEN ravnomernom raspodelom, jezgro podrazumevano 0)
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

- Svaki plan koji pošalješ Nikoli dodaj i u aplikaciju: `python3 -I minusi/uzivo/dodaj_plan.py <plan.txt> <sel.json> --oznaka "..." --kolo N`, pa objavi aplikaciju. Ručni generator u aplikaciji je isključen (GEN_OFF), kartica se zove „Ponuda i planovi“.

## Raspodela parova (analiza 14.11.2026)
`python3 minusi/analiza/raspodela.py --n 200 --izlaz minusi/analiza/raspodela_rezultat.txt`: isti odigrani parovi, isti tiketi i ulozi, samo drugačija izloženost. Na 24 dana (107.893 din): stvarno 155% vraćeno, ista izloženost nasumično 163%, ublaženo (koren) 184%, ravnomerno 206%. Pet najzastupljenijih parova po danu prošlo je 51%, svi parovi 57%. Zaključak: unutar užeg izbora rang ne razlikuje sigurnije od manje sigurnih parova; ravnomerna raspodela daje bolji prosek i manji raspon gubitka.

## STALNO PRAVILO od 14.11.2026: ravnomerna raspodela (odluka Nikole)
- `optg7.py` podrazumevano radi ravnomerno (`"ravnomerno": 1`): svaki IGRAČ ide na približno isti broj tiketa (prosek ±`tol`, podrazumevano 10%);
  njegove stavke dele tu kvotu. `maxu`/`pmax` iz cfg se tada zanemaruju, jezgro je 0. `"ravnomerno": 0` vraća staro.
- Veličina bazena: igrač je na (zbir dužina / broj igrača) tiketa. Da bude ≤25–30% tiketa: osmice ≥32 igrača, desetke ≥40. Optimizer upozorava preko 32%.
  Kad je ponuda mala (dan sa 3 utakmice), radije manje tiketa nego veće ponavljanje.
- Dužine (`minusi/analiza/raspodela2.py`, isti budžet, ravnomerno, 23 dana): osmice 220%, sedmice 193%, šestice 165%, desetke po 50 223%.
  Osmice > šestice u 16/23 dana (pouzdano), osmice > sedmice 13/23; desetke ≈ osmice. Osnova ostaju osmice, šestice izbegavati.
- Jezgro uz ravnomerno: 232% prema 216%, ali bolje samo 7/23 dana (P<0 ≈ 0,42), pa nije podrazumevano.
- Povraćaj (14.11.): proporcionalan ulogu. Tiketi od 9–10 parova do sada uvek 5x uloga (50 din → 250, 100 → 500), od 7–8 parova 1x–5x (prosek 2,5x).
  Sa tim (raspodela2.py): desetke po 50 229%, devetke po 50 231%, osmice po 50 215%, osmice po 100 207–220%, šestice 162%.
  Desetke nad osmicama bolje u 10/23 dana (P<0 ≈ 0,10): blaga prednost, nije sigurna. Šum simulacije je oko ±10 procentnih poena.

## Kolo 12, utorak 17.11.2026: plan (odluka Nikole 16.11.)
- Budžet 11.000 din, dva talasa, ravnomerno (optg7 podrazumevano). Bonus 14 parova 46% (potvrđeno), najmanji ulog 20 din (igramo ≥50), najveći dobitak 25 mil.
- Talas 1 (ujutru, prva ponuda): 50 osmica po 100 + 60 desetki po 50 (deo može devetke po 50) = 8.000.
- Talas 2 (popodne, posle zvaničnog izveštaja o povredama i nove ponude): 40 dvanaestica po 50 + 20 četrnaestica po 50 = 3.000; prednost spuštenim granicama.
- Za četrnaestice treba bar ~56 igrača u bazenu (≤25% tiketa po igraču); ako ih nema, prvo smanjiti četrnaestice.
- Šanse po tiketu (model 57–60% / do sada stvarno): osmica 1/69–1/47 / 1/97, desetka 1/180–1/115 / 1/276, dvanaestica 1/460–1/270, četrnaestica 1/1130–1/620 (`minusi/analiza/plan_sim.py`).

## Lista 20 najboljih minusa (od 17.11.2026)
- Redosled: prvo parovi gde se i minus-model slaže (`msig` ≥ 0,35, isto kao pravilo sajta) i forma nije protiv (ispod granice bar u polovini poslednjih 8), po verovatnoći spoja; ostali („samo model“) u drugom redu.
- Razlog: Vajli 17.11. bio prvi samo po spoju (69%) iako se minus-model nije slagao (0,29). Na vrhu dana (oko 3 po utakmici, kola 4–11, van uzorka) slaganje 69,1% (n=191), neslaganje 63,6% (n=44).
- Provereno i odbačeno: slabije skupljanje ka proseku pozicije za igrače bez prošle sezone (K_NOVI 10–40) i zamena stvarnim učinkom po minutu kad odstupa >20% kvare procenu (log verovatnoća, kola 4–11), pa model ostaje kakav jeste.
- Od 17.11.2026 (odluka Nikole): kad za duge tikete (12, 14) nema dovoljno igrača, bazen se širi igračima van modela, ali sa manjom težinom
  (`"tezine_igraca"` u cfg optg7: oba modela 1,0, jedan model 0,8, van modela 0,4). Bolje da igrač van modela bude na nekoliko tiketa
  nego da isti igrači budu na još više tiketa.

## Opseg poena igrača (Admiral specijal), 19.11.2026
- Ponuda: Specijali → Evroliga → Opseg poena igrača, po igraču 2–3 opsega od 5 poena (npr. 15–20 za 3,00). Pomoćnik v3 ih ubacuje (stavka `s:"R"`, `r:"15-20"`, `c` = šifra igrača sa liste).
- Kvote opsega su šablon po granici igrača (svi sa 11,5 imaju 2,50/3,10/4,30), ne zavise od kvota over/under ni od igrača. Zato su potcenjeni opsezi na strani na koju naginju tržište i naš model.
- Istorija (`spoj/analiza/opseg_istorija.py`, kola 6+, procena samo iz ranijih kola, uz pretpostavku da je šablon isti i ranije): svi opsezi naslepo −5% do −21%; opsezi sa procenjenom vrednošću ≥ +20%: povrat +47% do +61% (n 52–134), 7 od 7 kola u plusu. Neprovereno: šablon u ranijim kolima, pravilo granice (da li 15 ulazi u 10–15), limiti. Igrati kao probu malim ulogom i pratiti.

## 19.11.2026: ishod i nova pravila
- **Opseg: gornja granica se računa.** Shorts 20 poena na opsegu 15–20 je prošao (Nikolin tiket 9, 4 opsega, kvota 267,3, 100 din → isplaćeno 27.531 din, bonus oko 3% na 4 para). U `spoj/analiza/opseg*.py` važi tumačenje „sa gornjom“ (istorija: opsezi sa procenom ≥ +20% povrat oko +47%, n=134). Prvih 9 igrača opsega: 5 od 9 u opsegu (procena 30–40%).
- **Ponavljanje igrača najviše oko 22% tiketa (Nikola: „definitivno mora manje, možda i manje od 25%“).** U `optg7.py` parametar `maxpct` (podrazumevano 0,22) seče granicu svakog igrača bez obzira na težinu. Za to treba širi bazen (više igrača sa težinom 0,4) ili manje dugih tiketa.
- 19.11. minusi: nijedan dobitni od 74 iako po mestima 68% (asistencije 88%, skokovi 49%); pali su igrači sa 23 tiketa (Nunn, Washington, Wright). Parovi na 18+ tiketa 10/16, na 10–17 tiketa 9/12.

## 20.11.2026: dugo odsutni i raspored po dužinama (Nikola)
- Izostanak igrača koji ne igra već 5 ili više utakmica tima zaredom (sezonska povreda, svađa, duga pauza: Mike James, Dorsey, Deck, Montero) više se ne računa u filter izostanaka (`spoj/signali.py`, `DUGO_ODSUTAN = 5`). Tim se navikao bez njega.
- Raspored po dužinama: osmice što ravnomernije (ponavljanje ispod 20%) da na loš dan ne padnu sve i da redovno donose povraćaje; veći tiketi (desetke) sa više ponavljanja najjačih, kao bonus.
- Plan za 20.11. (duplo kolo, izuzetak): 5.000 din = 80 osmica + 20 desetki po 50; ubacuju se i igrači koji su blizu praga modela; ostatak za opsege.
