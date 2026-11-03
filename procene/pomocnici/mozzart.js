/* Pomoćnik za Mozzart: igrači Evrolige (poeni, skokovi, asistencije).
 *
 * Pokreće se kao bookmarklet na mozzartbet.com, na stranici Klađenje → Izdvojena ponuda → Igrači.
 * 0) Glavni način (proveren 3.11.2026): pomoćnik sam traži ponudu igrača od Mozzarta, istim zahtevom
 *    kao stranica (POST /betting/matches, zaglavlje Medium), za sve košarkaške takmičenja u ponudi „Igrači“.
 *    Igra se zove npr. „Broj poena E.Tubutis“ (stavka i igrač sa inicijalom), podigra „manje“/„više“,
 *    granica je specialOddValue, kvota value. Tim igrača se ne navodi, pa je t = „domaćin | gost“.
 * 1) Rezerva: od trenutka pokretanja hvata JSON odgovore koje stranica učitava (fetch i XHR).
 * 2) Ponovo učitava već učitane GET adrese ponude (iz performance liste), da uhvati i ono što je stiglo pre pokretanja.
 * 3) Dugme „Izvezi“ pravi snimak u formatu v2 (isti kao Admiral i MaxBet) i preuzima ga kao fajl.
 * 4) Dugme „Sirovo“ preuzima uhvaćene odgovore i tekst stranice, da bi se čitač prilagodio ako Mozzart promeni format.
 *
 * Ne hvata ništa vezano za nalog: adrese i ključevi koji liče na prijavu, nalog, stanje, tikete se preskaču.
 */
(function () {
  if (window.__mzPomocnik) { window.__mzPomocnik.prikazi(); return; }
  var V = '1';
  var uhvaceno = [];            // {url, metod, telo, vreme, podaci}
  var ZABRANJENO = /(login|logout|auth|token|session|account|nalog|user|profil|profile|balance|stanje|wallet|novcanik|payment|uplat|isplat|deposit|withdraw|ticket|tiket|kyc|notif|message|poruk|bonus|casino|kazino|chat)/i;
  var ZAB_KLJUC = /(token|email|mail|phone|telefon|jmbg|password|lozink|session|balance|username|address|adresa|iban|card)/i;

  function dobraAdresa(u) {
    try { var a = new URL(u, location.href); } catch (e) { return false; }
    if (!/mozzart/i.test(a.hostname)) return false;
    return !ZABRANJENO.test(a.pathname + a.search);
  }
  function ocisti(o, d) {
    d = d || 0;
    if (d > 40 || o === null || typeof o !== 'object') return o;
    if (Array.isArray(o)) return o.map(function (x) { return ocisti(x, d + 1); });
    var r = {};
    for (var k in o) { if (!ZAB_KLJUC.test(k)) r[k] = ocisti(o[k], d + 1); }
    return r;
  }
  function zapamti(url, metod, telo, tekst) {
    if (!dobraAdresa(url) || !tekst) return;
    var t = tekst.trim();
    if (t[0] !== '{' && t[0] !== '[') return;
    try { var j = JSON.parse(t); } catch (e) { return; }
    uhvaceno.push({ url: String(url), metod: metod, telo: telo && String(telo).slice(0, 2000), vreme: new Date().toISOString(), podaci: ocisti(j) });
    osvezi();
  }

  // presretanje fetch
  var stariFetch = window.fetch;
  window.fetch = function (ulaz, opcije) {
    var url = typeof ulaz === 'string' ? ulaz : (ulaz && ulaz.url);
    var metod = (opcije && opcije.method) || (ulaz && ulaz.method) || 'GET';
    var telo = opcije && opcije.body;
    return stariFetch.apply(this, arguments).then(function (odg) {
      try { odg.clone().text().then(function (t) { zapamti(url, metod, telo, t); }).catch(function () {}); } catch (e) {}
      return odg;
    });
  };
  // presretanje XHR
  var XO = XMLHttpRequest.prototype.open, XS = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.open = function (m, u) { this.__mz = { m: m, u: u }; return XO.apply(this, arguments); };
  XMLHttpRequest.prototype.send = function (b) {
    var x = this;
    if (x.__mz) x.__mz.b = b;
    x.addEventListener('load', function () {
      try {
        var t = (x.responseType === '' || x.responseType === 'text') ? x.responseText :
                (x.responseType === 'json' ? JSON.stringify(x.response) : null);
        zapamti(x.__mz.u, x.__mz.m, x.__mz.b, t);
      } catch (e) {}
    });
    return XS.apply(this, arguments);
  };

  // ponovno učitavanje već učitanih GET adresa ponude
  function dohvatiRanije() {
    var adrese = {};
    try {
      performance.getEntriesByType('resource').forEach(function (e) {
        if ((e.initiatorType === 'fetch' || e.initiatorType === 'xmlhttprequest') && dobraAdresa(e.name)) adrese[e.name] = 1;
      });
    } catch (e) {}
    Object.keys(adrese).forEach(function (u) {
      stariFetch(u, { credentials: 'include' }).then(function (r) { return r.text(); })
        .then(function (t) { zapamti(u, 'GET*', null, t); }).catch(function () {});
    });
  }

  // ---------- čitanje ponude iz uhvaćenih odgovora ----------
  function brojIliNista(x) {
    if (x === null || x === undefined || x === '') return null;
    var n = parseFloat(String(x).replace(',', '.'));
    return isFinite(n) ? n : null;
  }
  function stavka(t) {
    t = (t || '').toLowerCase();
    var p = /poen|points|\bpts\b/.test(t), s = /skok|rebound|\breb\b/.test(t), a = /asist|assist|\bast\b/.test(t);
    if (/trojk|three|3pt|3 poena/.test(t)) return null;
    if (p + s + a !== 1) return null;           // kombinacije (P+S, P+S+A) za sada ne
    return p ? 'P' : s ? 'S' : 'A';
  }
  function strana(t) {
    t = (t || '').toLowerCase().trim();
    if (/manje|ispod|under|\bmin\b|^-$|^\-|\(-\)/.test(t)) return 'u';
    if (/vi[sš]e|preko|over|\bmax\b|^\+$|^\+|\(\+\)/.test(t)) return 'o';
    return null;
  }
  function tekstoviObjekta(o) {
    var r = [];
    ['name', 'naziv', 'gameName', 'gameShortName', 'subGameName', 'subGameShortName', 'description', 'opis', 'label', 'caption', 'title', 'shortName', 'marketName', 'outcomeName', 'betName', 'tipName'].forEach(function (k) {
      if (typeof o[k] === 'string') r.push(o[k]);
    });
    ['subGame', 'game', 'market', 'outcome', 'tip', 'betType'].forEach(function (k) {
      if (o[k] && typeof o[k] === 'object') r = r.concat(tekstoviObjekta(o[k]));
    });
    return r;
  }
  function granica(o) {
    var kand = [o.specialOddValue, o.specialValue, o.sov, o.line, o.handicap, o.margin, o.limit, o.granica, o.sv,
                o.subGame && o.subGame.specialOddValue, o.game && o.game.specialOddValue];
    for (var i = 0; i < kand.length; i++) {
      var v = kand[i];
      if (v === undefined || v === null || v === '') continue;
      var m = String(v).match(/-?\d+(?:[.,]\d+)?/);
      if (m) { var n = brojIliNista(m[0]); if (n !== null && n > 0 && n < 100) return n; }
    }
    var tx = tekstoviObjekta(o).join(' ').match(/(\d{1,2}[.,]5)/);
    return tx ? brojIliNista(tx[1]) : null;
  }
  function kvota(o) {
    var kand = [o.value, o.odd, o.odds, o.price, o.ov, o.kvota, o.coefficient];
    for (var i = 0; i < kand.length; i++) {
      var n = typeof kand[i] === 'object' ? null : brojIliNista(kand[i]);
      if (n !== null && n > 1 && n < 100) return n;
    }
    return null;
  }
  function imeIgracaIzKonteksta(lanac) {
    // od najbližeg roditelja ka daljim: učesnici, home/away, ime igrača
    for (var i = lanac.length - 1; i >= 0; i--) {
      var o = lanac[i];
      if (!o || typeof o !== 'object' || Array.isArray(o)) continue;
      var kand = [o.playerName, o.player && (o.player.name || o.player.fullName), o.igrac, o.participantName];
      for (var j = 0; j < kand.length; j++) if (typeof kand[j] === 'string' && kand[j].length > 2) return { p: kand[j], o: o };
      if (Array.isArray(o.participants) && o.participants.length) {
        var imena = o.participants.map(function (x) { return x && (x.name || x.shortName || x.naziv); }).filter(Boolean);
        if (imena.length) return { p: imena[0], t: imena[1] || null, o: o };
      }
      if (typeof o.home === 'string' && typeof o.away === 'string') return { p: o.home, t: o.away, o: o };
      if (typeof o.home === 'object' && o.home && o.home.name && o.away && o.away.name) return { p: o.home.name, t: o.away.name, o: o };
    }
    return null;
  }
  function vremeIzKonteksta(o) {
    if (!o) return null;
    var v = o.startTime || o.kickOffTime || o.matchTime || o.start || o.date || o.time;
    if (typeof v === 'number') { var d = new Date(v > 1e12 ? v : v * 1000); return isNaN(d) ? null : d.toISOString(); }
    if (typeof v === 'string') return v;
    return null;
  }
  function citaj() {
    var mz = citajMozzart();
    if (mz.length) return oznaciGlavne(mz);
    var nadjeno = {};   // kljuc igrač|stavka|granica -> {p,t,s,l,u,o,c,time}
    function obidji(o, lanac, d) {
      if (d > 30 || !o || typeof o !== 'object') return;
      if (Array.isArray(o)) { for (var i = 0; i < o.length; i++) obidji(o[i], lanac, d + 1); return; }
      var k = kvota(o);
      if (k !== null) {
        var tx = tekstoviObjekta(o).join(' | ');
        var kontekst = imeIgracaIzKonteksta(lanac);
        var ctx = tx + ' | ' + (kontekst && kontekst.o ? tekstoviObjekta(kontekst.o).join(' | ') : '');
        var s = stavka(tx) || stavka(ctx), st = strana(o.subGameName || (o.subGame && o.subGame.subGameName) || o.name || o.outcomeName || o.shortName || tx);
        var l = granica(o);
        if (s && st && l !== null && kontekst) {
          var p = kontekst.p, t = kontekst.t || null;
          var m = String(p).match(/^(.*?)\s*\(([^)]+)\)\s*$/);   // "Ime Prezime (Tim)"
          if (m) { p = m[1]; t = t || m[2]; }
          var kl = p + '|' + s + '|' + l;
          var r = nadjeno[kl] || (nadjeno[kl] = { p: p, t: t, s: s, l: l, c: String((kontekst.o && (kontekst.o.code || kontekst.o.matchCode || kontekst.o.id)) || ''), time: vremeIzKonteksta(kontekst.o) });
          r[st] = k;
        }
      }
      lanac.push(o);
      for (var key in o) if (o[key] && typeof o[key] === 'object') obidji(o[key], lanac, d + 1);
      lanac.pop();
    }
    uhvaceno.forEach(function (u) { obidji(u.podaci, [], 0); });
    var picks = [];
    Object.keys(nadjeno).forEach(function (k) {
      var r = nadjeno[k];
      if (r.u && r.o) picks.push({ c: r.c, p: r.p, t: r.t, s: r.s, l: r.l, u: r.u, o: r.o, time: r.time });
    });
    return oznaciGlavne(picks);
  }
  function oznaciGlavne(picks) {
    // glavna granica po igraču i stavci: kvote najbliže jedna drugoj
    var grupe = {};
    picks.forEach(function (x) { var g = x.p + '|' + x.s + '|' + (x.t || ''); (grupe[g] = grupe[g] || []).push(x); });
    Object.keys(grupe).forEach(function (g) {
      var lst = grupe[g], best = lst.reduce(function (a, b) { return Math.abs(b.u - b.o) < Math.abs(a.u - a.o) ? b : a; });
      lst.forEach(function (x) { x.m = x === best ? 1 : 0; });
    });
    picks.sort(function (a, b) { return (a.t || '').localeCompare(b.t || '') || a.p.localeCompare(b.p) || a.s.localeCompare(b.s) || a.l - b.l; });
    return picks;
  }


  // ---------- glavni način: zahtev ka Mozzartu ----------
  var aktivno = { n: 0, greska: null, takmicenja: {} };
  function mzStore() {
    try { var el = document.getElementById('spa'); return el && el.__vue__ && el.__vue__.$store && el.__vue__.$store.state.BettingNew; } catch (e) { return null; }
  }
  function preuzmiAktivno() {
    var st = mzStore();
    if (!st || !st.payloadFilter) { aktivno.greska = 'Otvori Klađenje → Izdvojena ponuda → Igrači, pa pokreni ponovo.'; osvezi(); return Promise.resolve(); }
    var osnova = {};
    for (var k in st.payloadFilter) osnova[k] = st.payloadFilter[k];
    delete osnova.competitionIds;                    // sva takmičenja iz ponude „Igrači“
    osnova.loadPriorityTemplateGamesOnly = false; osnova.loadAllTemplateGames = true; osnova.packAllGroups = true;
    osnova.pageSize = 50;
    var medium = st.medium || 'PREMATCH_WEB';
    function zahtev(f) {
      return stariFetch('/betting/matches', { method: 'POST', credentials: 'include',
        headers: { 'Content-Type': 'application/json', 'Medium': medium }, body: JSON.stringify(f) })
        .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); });
    }
    function kopija(dod) { var f = {}; for (var k in osnova) f[k] = osnova[k]; for (var k2 in dod) f[k2] = dod[k2]; return f; }
    // 1) spisak utakmica u ponudi „Igrači“ (bez takmičenja) da se nađu košarkaška takmičenja;
    // 2) ponuda po takmičenju (bez competitionIds Mozzart vraća pogrešne igre za košarku)
    function takmicenje(id, n) {
      return zahtev(kopija({ competitionIds: [id], currentPage: n })).then(function (d) {
        var items = (d.items || []).filter(function (it) { return !it.sport || it.sport.id === 2; });
        items.forEach(function (it) { var c = it.competition && it.competition.name; if (c) aktivno.takmicenja[c] = (aktivno.takmicenja[c] || 0) + 1; });
        uhvaceno.push({ url: 'aktivno:/betting/matches#' + id + '/' + n, metod: 'POST', vreme: new Date().toISOString(), podaci: ocisti({ items: items }) });
        aktivno.n += items.length;
        if ((d.items || []).length >= 50 && n < 9) return takmicenje(id, n + 1);
      });
    }
    aktivno.greska = null; aktivno.takmicenja = {};
    return zahtev(kopija({ currentPage: 0 })).then(function (d) {
      var ids = [];
      (d.items || []).forEach(function (it) {
        if (it.sport && it.sport.id === 2 && it.competition && ids.indexOf(it.competition.id) < 0) ids.push(it.competition.id);
      });
      if (!ids.length && st.payloadFilter.competitionIds) ids = st.payloadFilter.competitionIds.slice();
      return ids.reduce(function (pr, id) { return pr.then(function () { return takmicenje(id, 0); }); }, Promise.resolve());
    }).catch(function (e) { aktivno.greska = 'Mozzart nije vratio ponudu (' + e.message + ').'; }).then(osvezi);
  }
  var ST_MZ = { poena: 'P', poeni: 'P', skokova: 'S', skokovi: 'S', asistencija: 'A', asistencije: 'A' };
  function citajMozzart() {
    var out = {};
    uhvaceno.forEach(function (u) {
      (((u.podaci || {}).items) || []).forEach(function (it) {
        if (!it || !it.oddsGroup) return;
        var t = ((it.home && it.home.name) || '') + ' | ' + ((it.visitor && it.visitor.name) || '');
        it.oddsGroup.forEach(function (g) {
          (g.odds || []).forEach(function (o) {
            var gm = (o.game && o.game.name) || '';
            // npr. „Broj poena E.Tubutis“; za skokove i asistencije očekuje se isti oblik
            var m = gm.match(/(poena|poeni|skokova|skokovi|asistencija|asistencije)\s+(.+)$/i);
            if (!m || /\+|ukupno .* i /i.test(gm)) return;
            var sub = ((o.subgame && o.subgame.name) || '').toLowerCase();
            var st = /manje/.test(sub) ? 'u' : /vi[sš]e/.test(sub) ? 'o' : null;
            var l = brojIliNista(o.specialOddValue), kv = brojIliNista(o.value);
            if (!st || l === null || kv === null || kv <= 1) return;
            var s = ST_MZ[m[1].toLowerCase()], p = m[2].trim(), kl = p + '|' + s + '|' + l + '|' + t;
            var r = out[kl] || (out[kl] = { c: String(it.matchNumber || it.id || ''), p: p, t: t, s: s, l: l,
              time: it.startTime ? new Date(it.startTime).toISOString() : null, liga: it.competition && it.competition.name });
            r[st] = kv;
          });
        });
      });
    });
    return Object.keys(out).map(function (k) { return out[k]; }).filter(function (r) { return r.u && r.o; });
  }

  // ---------- izvoz ----------
  function dan() {
    var d = new Date(); return d.getFullYear() + '-' + ('0' + (d.getMonth() + 1)).slice(-2) + '-' + ('0' + d.getDate()).slice(-2);
  }
  function satMin() { var d = new Date(); return ('0' + d.getHours()).slice(-2) + ('0' + d.getMinutes()).slice(-2); }
  function preuzmi(ime, obj) {
    var b = new Blob([JSON.stringify(obj)], { type: 'application/json' });
    var a = document.createElement('a'); a.href = URL.createObjectURL(b); a.download = ime;
    document.body.appendChild(a); a.click(); setTimeout(function () { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  function izvezi() {
    var picks = citaj();
    if (!picks.length) { poruka('Nije pronađena nijedna granica. Otvori ponudu igrača Evrolige, sačekaj da se učita i pokušaj ponovo. Ako i dalje ne radi, preuzmi „Sirovo“ i pošalji ga.'); return; }
    preuzmi(dan() + '_mozzart_' + satMin() + '.json', { v: 2, src: 'mozzart', at: new Date().toISOString(), pomocnik: V, picks: picks, el: null });
    poruka('Izvezeno: ' + picks.length + ' granica, ' + new Set(picks.map(function (x) { return x.p; })).size + ' igrača.');
  }
  function sirovo() {
    var tekst = '';
    try { tekst = (document.querySelector('main') || document.body).innerText.slice(0, 300000); } catch (e) {}
    preuzmi('mozzart_sirovo_' + dan() + '_' + satMin() + '.json', { v: 1, src: 'mozzart-sirovo', at: new Date().toISOString(), pomocnik: V, strana: location.pathname, odgovori: uhvaceno, tekst: tekst });
  }

  // ---------- panel ----------
  var panel = document.createElement('div');
  panel.style.cssText = 'position:fixed;z-index:2147483647;right:12px;bottom:12px;width:300px;background:#111;color:#eee;font:13px/1.4 system-ui,sans-serif;border-radius:10px;box-shadow:0 6px 24px rgba(0,0,0,.4);padding:12px';
  panel.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px"><b>Mozzart pomoćnik</b><span data-x style="cursor:pointer;padding:0 4px">✕</span></div>' +
    '<div data-st style="margin-bottom:8px;color:#bbb"></div>' +
    '<div data-msg style="margin-bottom:8px;color:#fd6"></div>' +
    '<div style="display:flex;gap:6px"><button data-iz style="flex:1;padding:6px;border:0;border-radius:6px;background:#f5c518;color:#111;font-weight:600;cursor:pointer">Izvezi</button>' +
    '<button data-sir style="flex:1;padding:6px;border:0;border-radius:6px;background:#333;color:#eee;cursor:pointer">Sirovo</button></div>';
  document.body.appendChild(panel);
  function poruka(t) { panel.querySelector('[data-msg]').textContent = t; }
  function osvezi() {
    var picks = citaj();
    var tak = Object.keys(aktivno.takmicenja).map(function (k) { return k + ' ' + aktivno.takmicenja[k]; }).join(', ');
    panel.querySelector('[data-st]').textContent = 'Granica: ' + picks.length + ' · igrača: ' + new Set(picks.map(function (x) { return x.p + x.t; })).size +
      (tak ? ' · utakmice: ' + tak : '') + (aktivno.greska ? ' · ' + aktivno.greska : '');
    var ev = picks.filter(function (x) { return /evroliga|euroleague/i.test(x.liga || ''); }).length;
    if (picks.length && !ev && Object.keys(aktivno.takmicenja).length) poruka('U ponudi „Igrači“ trenutno nema Evrolige; izvoz će sadržati ostala takmičenja.');
  }
  panel.querySelector('[data-x]').onclick = function () { panel.style.display = 'none'; };
  panel.querySelector('[data-iz]').onclick = function () { preuzmiAktivno().then(izvezi); };
  panel.querySelector('[data-sir]').onclick = sirovo;
  window.__mzPomocnik = { prikazi: function () { panel.style.display = 'block'; osvezi(); }, citaj: citaj, uhvaceno: uhvaceno };
  osvezi();
  poruka('Učitavam ponudu igrača sa Mozzarta…');
  preuzmiAktivno().then(function () { if (!aktivno.greska) poruka('Spremno. Klikni Izvezi.'); else poruka(aktivno.greska); });
})();
