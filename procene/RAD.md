# Procene: dnevni rad i dogovorena pravila (za nastavak u novom razgovoru ili nalogu)

Pročitaj prvo `CLAUDE.md` (korisnik, jezik, granice projekata) i `procene/README.md` (skripte i model).
Ovaj fajl je sažetak kako se radi iz dana u dan i šta je dogovoreno sa Nikolom (stanje 5.11.2026).

## Izvori

- Koji sajtovi rade i kako se čitaju: `procene/IZVORI.md`. Pri analizi i pravljenju predloga otvarati vesti, povrede i
  sastave (Eurohoops, BasketNews, Evroliga), ne samo podatke iz repozitorijuma (Nikola, 6.11.2026).

## Granice

- Pišeš samo u `procene/` i u `baza/ponude/<kladionica>/` kad Nikola pošalje ponudu ili je ti povučeš.
- `minusi/` je Nikolina lična igra: ne koristi se i ne menja (izuzetak: pomoćnici za tikete, samo za čitanje, kad on traži).
- Javni sajt: repozitorijum `nikolapakic11/evroliga-plus-minus` (GitHub Pages), pravi ga `procene/skripte/sajt.py`.
- Pre svakog slanja: `git pull --rebase`, pa `git push`. Na kraju commit poruke atribucija koju sesija traži.

## Dan utakmice

Zakazani zadaci su isključeni (odluka 5.11.2026): ništa se ne pokreće samo. Svaki korak ispod radi se ručno, kad Nikola pošalje ponude ili zatraži u razgovoru. Ne praviti nove zakazane zadatke bez njegovog izričitog zahteva.


1. Nikola pošalje ponude Admirala i MaxBeta (JSON iz njegovih pomoćnika, `{"v":2,"src":...,"picks":[...]}`).
   Sačuvaj ih kao `baza/ponude/admiral/<dan>_<slovo>.json` i `baza/ponude/maxbet/<dan>_<slovo>.json` (slova a, b, c po redu).
   Ako pošalje plan tiketa (`{"v":1,"tickets":...}`), to nije ponuda.
2. Mozzart: odbija pristup iz radnog okruženja, čita se preko Chrome-a (alat Claude in Chrome):
   `procene/alati/mozzart_citac.js` (uputstvo u fajlu), pa `python3 procene/skripte/mozzart_unos.py <fajl>`.
   Bolji su pojedinačni mečevi (`/match/<ID>?mtid=2`) nego zbirna stranica.
3. Soccerbet ide sam (`soccerbet.py`, poziva ga `dan.py`).
4. `python3 procene/skripte/dan.py` (pre 12h sa `--jutro`): dopuna ishoda, statistika, sastavi, povrede, Soccerbet, tabla, predlozi.
   Na kraju ispiše PREGLED (i red RUČNO ako fale ponude).
5. Commit i push, `python3 procene/skripte/sajt.py /home/claude/evroliga-plus-minus`, commit i push sajta.
   Zatim objavi `procene/javno/predlozi.html` na artefakt https://claude.ai/artifact/HUT71aS4AnLVknR6pKgpDv
   (napravljen na starom nalogu, podeljen sa novim uz pravo uređivanja; objava na isti URL).

## Pravila objave (dogovoreno)

- Dubinska analiza svakog predloga pre objave (Nikola, 6.11.2026: „krem de la krem“): za svakog kandidata poslednjih 8
  utakmica (minuti i stavka), domaća liga, ranije protiv istog protivnika, odbrana protivnika po poziciji, ko se vraća ili
  nedostaje u oba tima (izveštaj o povredama, vesti, novi igrači), razlika granica među kladionicama. Izbaciti
  (`procene/podaci/iskljuceni.json`, sa razlogom) sve gde kontekst ide protiv ili je oko 50%; bolje manje, a sigurnije.

- Konsultacija pre objave (odluka 6.11.2026): kad Nikola pošalje ponude, pokreni `dan.py`, pokaži mu predloge za dan
  u razgovoru (sa razlozima i upozorenjima) i objavi na sajt i artefakt TEK kad on potvrdi.

- Ništa pre 12h na dan utakmice. Ranija objava samo kad Nikola traži: `procene/podaci/objava.json` `{"<dan>": "HH:MM"}`.
- Konačni predlozi: sat pre prve utakmice dana ako počinje pre 18h, inače sat i po pre (zajedno.rokovi).
  Konačno je ono što je objavljeno u tom trenutku; posle se ne menja. Učinak se računa samo za konačne.
- Predlozi za dan (od 6.11.2026, posle podne): rang po PREDNOSTI nad tržištem (naša verovatnoća − fer verovatnoća iz kvota
  svih kladionica). Ulazi strana sa prednošću bar 4 poena i verovatnoćom bar 54%, najmanje 4, najviše 12; najviše 4 iz
  utakmice, 2 iz tima, 3 sa kvotom ispod 1,65. PLUS nije obavezan; do 2 najbolja PLUS sa bar 54% i prednošću bar 2 poena.
  Razlog (Nikola): po samoj verovatnoći izbor ide na najniže kvote, a to može svako. Provera: `procene/provera/kvote_2026-11-06.txt`
  (po prednosti 60,6%, +17,8%, kvota 1,95; po verovatnoći 60,8%, +2,3%, kvota 1,69).
- Spajanje (od 6.11.2026): novija kola imaju veću težinu (0,55 po kolu unazad), slobodni član prema stopi preko u
  poslednja 2 kola (stopa preko raste kroz sezonu: kola 4–5 oko 39%, 8–10 oko 49%).
- Forma: predlog ulazi samo ako je igrač u bar polovini poslednjih 7 utakmica bio na toj strani granice.
- Već objavljen predlog ostaje dok ga novi ne nadmaši za 2 poena procenta (da lista ne skače).
- Povučeni i izmenjeni predlozi ostaju u Istoriji sa vremenom i ishodom; ne ulaze u učinak.

## Povrede i odsutni (samo potvrđeno)

- Novajlija (od 6.11.2026, Nikola, primer Lonnie Walker): igrač čiji je prvi meč za tim u poslednje 4 utakmice tima i ima bar 2:
  minuti = ponderisani prosek (prva utakmica 0,3, ostale 1, plus prosek minuta iz prošle sezone Evrolige), a može u predlog
  već posle 2 utakmice ako ima prošlu sezonu. Izostanak iz poslednje 3 ne isključuje igrača kog izveštaj potvrđuje („igra“).
  Kod novih igrača pogledati i njihovu istoriju (prethodni klubovi u Evroligi, domaća liga, vesti o ulozi) pre predloga;
  ako je jasno da će uloga biti veća od proseka, predložiti Nikoli ručne minute (`procene/minuti.json`).

- Povratak i odsustvo saigrača (od 6.11.2026, `procene/skripte/prilagodjavanje.py`, pravilo NOVO): blago (povratak
  w = n/(n+4), odnos 0,85–1,15; od odsutnog 40% minuta, najviše +4 min po igraču; ukupno ±12%), korist po minutu
  (+4% P i A) samo glavnoj opciji tima, ostali samo minute. Za izbor predloga važi manja verovatnoća od dve
  (sa i bez prilagođavanja): prilagođavanje ne može samo da stvori ili pojača predlog. Provera: `procene/provera/provera_2026-11-06.md`.

- Izvori: zvanični izveštaj Evrolige preko Eurohoops i dnevni izveštaj BasketNews-a
  (https://basketnews.com/leagues/25-euroleague/injured.html, ima prednost). `povrede.py` čita oba.
- Igrač kojeg nema u ponudi kladionica NIJE odsutan (kladionice izbacuju igrače sa malim granicama). Nikola to traži izričito.
- Ručne potvrde (npr. Nikola kaže da igrač igra): `procene/podaci/povrede_rucno.json`.
- Potvrđeno odsutan igrač iz rotacije: njegov tim ne dobija MINUS, a model deli njegove minute saigračima.
- Nova pojačanja koja mogu da debituju (izveštaj „New signing ... registered“): bez PLUS za igrače iste pozicije u tom timu.
- U obrazloženjima nikad ne tvrditi da neko ne igra ako nije potvrđeno.

## Sajt

- Kartice: Predlozi, Istorija (po utakmici: predlozi, povučeni, cela ponuda dana sa očekivanjem i stvarnim učinkom),
  Igrači (napredno: očekivanja), Statistika, Kako radi.
- Timovi sa zvaničnim skraćenicama Evrolige (tvCode: EFS, RMB, PAO, FBT, KBA, PBB, BAY, VBC, CZV, MTA, BJK ...).
- Učinak: po danu broj predloga i koliko je prošlo (npr. 5/6 · 83%), bez jedinica i nivoa.
- Obrazloženja ljudskim jezikom, bez procenata i matematike.

## Tiketi (Nikolina igra, odvojeno od sajta)

- Planovi se čuvaju u `procene/tiketi/`. Admiral pomoćnik: `{"v":1,"round":"","tickets":[{"stake":..,"legs":[{c,p,t,s,l,u,d}]}]}`,
  `"d":"O"` je plus (preko), bez `d` minus. MaxBet pomoćnik v3 (čita i pluseve): `procene/alati/maxbet_pomocnik_v3_obelezivac.txt`
  (izvor `maxbet_pomocnik_v3.js`); na MaxBetu: plus poeni „Igrač postiže više poena“, skokovi/asistencije SK+/AS+.
- Sistemski tiketi na Admiralu se ne isplate (ogroman ulog za 7/10 i slično).

## Otvoreno

- Model skuplja učinak po minutu ka proseku pozicije kad igrač nema prošlu sezonu u Evroligi (dolasci iz NBA, svi igrači
  Bešiktaša). 6.11.: Morgan precenjen (vučen ka centrima, 4,6 naspram 2,9), Valančiunas potcenjen (6,3 naspram 8,1).
  Proveriti slabije skupljanje za takve igrače ili spoljnu prethodnu statistiku (NBA, domaće lige) i predložiti Nikoli.

- Senka (odluka 5.11.2026): od kola 11 `senka.py` uporedo beleži predloge po varijanti „skupljanje samo nadole“
  (model ispod proseka igrača: 0,7·model + 0,3·prosek) u `procene/senka/`, bez prikaza. Posle 3 kola sa ishodima
  (otprilike posle kola 13) PREGLED u `dan.py` ispisuje PODSETNIK: tada Nikoli pokaži poređenje i predloži odluku.
  Razlozi: `procene/provera/provera_2026-11-05.md`. Obavezni PLUS ostaje; filter poena za igrače sa malo minuta odbačen.
- Kad god rezultati nekog dela (PLUS, stavka, nivo) dugo odstupaju od provere, ili se nakupi novih ishoda za ponovnu
  proveru, predloži Nikoli analizu (on to traži, 5.11.2026).

- Minuti tima: svođenje na 200 se NE uvodi (provera u `procene/provera/minuti_tima.md`); prati se pravilo „tim sa
  pretrpanom rotacijom (zbir preko 225) bez MINUS-a“, pa pitati Nikolu jednostavnim rečima.
- Presek tiketa i predloga posle utakmica: ishodi se upisuju sa `dopuna.py` + `predlozi.py` (radi i dok je utakmica završena a zapisnik još „uživo“).
