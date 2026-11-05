// Mozzart čitač: igrači Evrolige sa stranice utakmice (mtid=2), preko Chrome-a (Mozzart odbija pristup iz radnog okruženja).
// 1) Na https://www.mozzartbet.com/sr/kladjenje/sport/2 nađi ID utakmica Evrolige (linkovi /match/<ID>).
// 2) Za svaku utakmicu otvori https://www.mozzartbet.com/sr/kladjenje/sport/2/match/<ID>?mtid=2, sačekaj 3 s i pokreni ovo.
// 3) Rezultat (red po utakmici) zalepi u fajl kao "<ID>@<Domaćin> - <Gost>#<rezultat>" i pretvori: python3 procene/skripte/mozzart_unos.py <fajl>
(() => {
  const L = document.body.innerText.split('\n').map(x => x.trim()).filter(Boolean);
  const out = []; let cur = null, l = null;
  for (let i = 0; i < L.length; i++) {
    const x = L[i];
    const m = x.match(/^Broj (poena|skokova|asistencija) (.+)$/);
    if (m && m[2] !== 'igrača') { cur = { s: { poena: 'P', skokova: 'S', asistencija: 'A' }[m[1]], p: m[2] }; continue }
    if (/^(Poeni|Broj|Ukupno)/.test(x)) { cur = null; continue }
    if (!cur) continue;
    if (/^\d+(\.\d+)?$/.test(x) && L[i + 1] === 'manje') { l = +x; continue }
    if (x === 'manje') { out.push([cur.p, cur.s, l, +L[i + 1], L[i + 2] === 'više' ? +L[i + 3] : null].join('|')); i += 3 }
  }
  return out.join(';');   // izlaz je dug; iz alata čitati u delovima (npr. .slice(0,900), .slice(900,1800) ...)
})()
