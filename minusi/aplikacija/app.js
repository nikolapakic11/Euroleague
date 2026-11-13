
(function(){
  var HEAD = '<meta charset="utf-8">\n<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n<title>Evroliga minusi</title>\n<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n<link href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&display=swap" rel="stylesheet">';
  var SC = 'scr' + 'ipt';

  function $(s){ return document.querySelector(s); }
  function esc(v){ return String(v == null ? '' : v).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function num(v){ if (v === '' || v == null) return null; var n = parseFloat(String(v).replace(',', '.')); return isFinite(n) ? n : null; }
  function fmt(n, d){ if (d == null) d = 2; return (n == null || !isFinite(n)) ? '–' : n.toLocaleString('sr-RS', {minimumFractionDigits:d, maximumFractionDigits:d}); }
  function pct(n){ return (n == null || !isFinite(n)) ? '–' : (n * 100).toFixed(1).replace('.', ',') + '%'; }
  function signed(n){ return (n > 0 ? '+' : '') + fmt(n); }
  function today(){ var d = new Date(); d.setMinutes(d.getMinutes() - d.getTimezoneOffset()); return d.toISOString().slice(0,10); }
  function uid(){ return Date.now().toString(36) + Math.random().toString(36).slice(2,7); }
  function clone(o){ return JSON.parse(JSON.stringify(o)); }
  var STAT = {P:'Poeni', A:'Asistencije', S:'Skokovi'};
  function parova(n){ var m10 = n % 10, m100 = n % 100; return n + (m10 === 1 && m100 !== 11 ? ' par' : (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) ? ' para' : ' parova'); }

  var state;
  try { state = JSON.parse($('#state').textContent); } catch(e) { state = null; }
  if (!state || !Array.isArray(state.tickets)) state = {v:1, savedAt:0, tickets:[], results:{}, players:{}};
  state.results = state.results || {}; state.players = state.players || {};

  function blankLeg(){ return {p:'', team:'', stat:'P', line:'', odds:''}; }
  function blankDraft(){
    var last = state.tickets[state.tickets.length - 1];
    return {date: today(), round: last ? String(last.round) : '', stake: last ? String(last.stake) : '', fund: last && last.fund === 'dobitak' ? 'dobitak' : 'novi', legs:[blankLeg(), blankLeg(), blankLeg()]};
  }

  var ui = {tab:'novi', draft:null, resDraft:{}, resRound:'', showSettled:false, tFilter:'all', tLimit:40, open:{}, paste:false, err:'', queue:[], pendingQ:[]};
  var flash = '';
  try {
    var savedUi = JSON.parse(sessionStorage.getItem('mt-ui') || 'null');
    var pending = +sessionStorage.getItem('mt-pending') || 0;
    if (savedUi) {
      ui = Object.assign(ui, savedUi);
      if (pending) {
        if ((state.savedAt || 0) >= pending) { ui.draft = null; ui.resDraft = {}; var pq = ui.pendingQ || []; ui.queue = (ui.queue || []).filter(function(q){ return pq.indexOf(q.id) < 0; }); flash = sessionStorage.getItem('mt-flash') || 'Sačuvano.'; }
        else { flash = 'Neko je u međuvremenu sačuvao noviju verziju. Tvoj unos je zadržan, sačuvaj ponovo.'; }
      }
    }
    sessionStorage.removeItem('mt-pending'); sessionStorage.removeItem('mt-flash');
  } catch(e) {}
  ui.err = ''; ui.pendingQ = []; ui.queue = (ui.queue || []).map(function(q){ if (q.status === 'waiting' || q.status === 'working') { q.status = 'error'; q.msg = 'Čitanje je prekinuto. Izaberi sliku ponovo.'; } return q; });
  if (!ui.draft) ui.draft = blankDraft();
  function saveUi(){ try { sessionStorage.setItem('mt-ui', JSON.stringify(ui)); } catch(e) {} }

  /* ---------- storage ---------- */
  var mode = 'loading'; // artifact | local | readonly
  var busy = false;
  var capP = (window.claude && typeof window.claude.use === 'function')
    ? window.claude.use('artifact').catch(function(){ return null; })
    : Promise.resolve(null);
  capP.then(function(ns){
    mode = ns ? 'artifact' : 'local';
    if (!ns) loadLocal();
    render();
  });

  var sampleFn = null, imgLimits = null, running = 0, filesMem = {}, scanState = 'checking';
  var sampleP = (window.claude && typeof window.claude.use === 'function')
    ? window.claude.use('sample').catch(function(){ return null; })
    : Promise.resolve(null);
  sampleP.then(function(fn){
    if (!fn) { scanState = 'nosample'; renderScan(); return; }
    sampleFn = fn; scanState = 'ok';
    return fn.limits().then(function(l){ imgLimits = l && l.images || null; renderScan(); }, function(){ renderScan(); });
  });

  function matchPlayer(name){
    var n = name.trim().toLowerCase(); if (!n) return null;
    var names = Object.keys(state.players), hit = null, count = 0;
    for (var i = 0; i < names.length; i++) { if (names[i].toLowerCase() === n) return names[i]; }
    names.forEach(function(k){
      var parts = k.toLowerCase().split(/\s+/), last = parts[parts.length - 1];
      var np = n.replace(/\./g, '').split(/\s+/), nl = np[np.length - 1];
      if (last === nl || last === n) { hit = k; count++; }
    });
    return count === 1 ? hit : null;
  }
  function scanPrompt(){
    var known = Object.keys(state.players).slice(0, 400);
    return 'This image is a photo or screenshot of a sports betting slip from a Serbian bookmaker (for example Mozzart, Meridian, MaxBet, Soccerbet, Admiral, Balkan Bet). ' +
      'It contains Euroleague basketball player prop bets on points, assists and rebounds. Extract every bet on the slip.\n\n' +
      'Serbian terms: poeni, poena = points; asistencije, asist = assists; skokovi, skok = rebounds. "manje", "ispod", "U", "-" = under; "više", "preko", "O", "+" = over. ' +
      'Kvota = odds, ulog or uplata = stake, dobitak = payout. Numbers may use a decimal comma.\n\n' +
      'Reply with only this JSON: {"readable": true, "date": "YYYY-MM-DD or null", "stake": number or null, "totalOdds": number or null, ' +
      '"legs": [{"player": "name as printed", "team": "team if printed, else empty string", "stat": "P for points, A for assists, S for rebounds, X for anything else", "direction": "under or over", "line": 12.5, "odds": 1.85}]}\n' +
      'List the legs in the order they appear. Never guess a value you cannot read: use null for it. If the image is not a betting slip or is unreadable, reply {"readable": false, "legs": []}.' +
      (known.length ? '\n\nKnown players. When the slip clearly refers to one of these, use exactly this spelling: ' + known.join(', ') : '');
  }
  function normalizeScan(r){
    var warn = [], legs = [];
    if (!r || r.readable === false || !Array.isArray(r.legs)) return {ticket:{legs:[]}, warn:['Slika nije prepoznata kao tiket.']};
    r.legs.forEach(function(l, i){
      var n = i + 1, stat = String(l && l.stat || '').toUpperCase(), line = num(l && l.line), odds = num(l && l.odds), p = String(l && l.player || '').trim();
      if (!p || line == null || odds == null || odds <= 1) { warn.push('Par ' + n + (p ? ' (' + p + ')' : '') + ' nije potpuno pročitan.'); return; }
      if (['P','A','S'].indexOf(stat) < 0) { warn.push('Par ' + n + ' (' + p + ') nije poeni, asistencije ni skokovi.'); return; }
      if (String(l.direction || '').toLowerCase() === 'over') { warn.push('Par ' + n + ' (' + p + ') je plus, a ne minus.'); return; }
      var known = matchPlayer(p) || p;
      legs.push({p: known, team: String(l.team || '').trim() || state.players[known] || '', stat: stat, line: String(line), odds: String(odds)});
    });
    var prod = legs.reduce(function(a, l){ return a * num(l.odds); }, 1), tot = num(r.totalOdds);
    if (tot && legs.length && !warn.length && Math.abs(prod - tot) / tot > 0.02) warn.push('Ukupna kvota sa tiketa (' + fmt(tot) + ') se ne slaže sa proizvodom kvota (' + fmt(prod) + '). Proveri kvote.');
    var stake = num(r.stake);
    return {ticket:{date: /^\d{4}-\d{2}-\d{2}$/.test(r.date || '') ? r.date : today(), stake: stake != null && stake > 0 ? String(stake) : '', totalOdds: tot, legs: legs}, warn: warn};
  }
  function addFiles(list){
    var files = Array.prototype.slice.call(list || []);
    files.forEach(function(f){
      var id = uid(), item = {id: id, name: f.name || 'slika', status: 'waiting', msg: '', warn: [], ticket: null};
      filesMem[id] = f;
      ui.queue.push(item);
    });
    saveUi(); renderScan(); pump();
  }
  function pump(){
    while (running < 2 && sampleFn) {
      var it = ui.queue.filter(function(q){ return q.status === 'waiting' && (filesMem[q.id] || q.text); })[0];
      if (!it) break;
      running++; it.status = 'working'; it.msg = '';
      readTicket(it).then(function(){ running--; saveUi(); renderScan(); pump(); });
    }
    renderScan();
  }
  var TERMS = 'Serbian terms: poeni, poena = points; asistencije, asist = assists; skokovi, skok = rebounds. "manje", "ispod", "U", "-" = under; "više", "preko", "O", "+" = over. ' +
    'Kvota = odds, ulog or uplata = stake, dobitak = payout. Numbers may use a decimal comma.\n\n';
  var TICKET_SHAPE = '{"readable": true, "date": "YYYY-MM-DD or null", "stake": number or null, "totalOdds": number or null, ' +
    '"legs": [{"player": "name as printed", "team": "team if printed, else empty string", "stat": "P for points, A for assists, S for rebounds, X for anything else", "direction": "under or over", "line": 12.5, "odds": 1.85}]}';
  function knownTxt(){ var known = Object.keys(state.players).slice(0, 400); return known.length ? '\n\nKnown players. When a slip clearly refers to one of these, use exactly this spelling: ' + known.join(', ') : ''; }
  function longPrompt(n, kind){
    var src = kind === 'pdf' ? 'of a PDF document (in reading order, page after page) exported from a Serbian bookmaker' : 'of a screenshot or photo from a Serbian bookmaker app, website or paper slip';
    return (n > 1 ? 'These ' + n + ' images are consecutive vertical parts, in order from top to bottom, ' : 'This image is one part ') +
      src + ', showing one or more betting slips (tickets). ' +
      (n > 1 ? 'Neighbouring parts overlap a little, so the same lines can appear at the bottom of one part and the top of the next: count them once. ' : '') +
      'The tickets contain Euroleague basketball player prop bets on points, assists and rebounds.\n\n' +
      'Extract every ticket whose bets are fully visible in ' + (n > 1 ? 'these images' : 'this image') + '. ' +
      'Skip a ticket whose bets are cut off at the very top of the first image or the very bottom of the last image; it is read in another pass. Keep each ticket separate and never merge bets from two tickets.\n\n' +
      TERMS +
      'Reply with only compact JSON, no spaces or line breaks, in this exact shape:\n' +
      '{"t":[{"d":"2026-09-24","s":200,"o":45.3,"l":[["Hezonja","P","U",12.5,1.85],["Lessort","A","U",1.5,1.9]]}]}\n' +
      'Per ticket: d = date YYYY-MM-DD or null, s = stake or null, o = total odds or null, l = bets. ' +
      'Per bet: [player name as printed, "P" points / "A" assists / "S" rebounds / "X" anything else, "U" under / "O" over, line, odds]. ' +
      'Use null for any value you cannot read, never guess. If there is no complete ticket, reply {"t":[]}.' + knownTxt();
  }
  function fromCompact(tk){
    if (!tk || !Array.isArray(tk.l)) return null;
    return {readable: true, date: tk.d || null, stake: tk.s, totalOdds: tk.o, legs: tk.l.map(function(b){
      b = Array.isArray(b) ? b : [];
      return {player: b[0] == null ? '' : String(b[0]), team: '', stat: b[1], direction: String(b[2] || '').toUpperCase() === 'O' ? 'over' : 'under', line: b[3], odds: b[4]};
    })};
  }
  function sigOf(legs, stake){
    return legs.map(function(l){ return [String(l.p).trim().toLowerCase(), l.stat, num(l.line), num(l.odds)].join('|'); }).sort().join('~') + '#' + (num(stake) || '');
  }
  function decodeImg(f){
    if (window.createImageBitmap) return createImageBitmap(f).then(function(b){ return {src:b, width:b.width, height:b.height, close:function(){ try { b.close(); } catch(e) {} }}; });
    return new Promise(function(res, rej){
      var url = URL.createObjectURL(f), im = new Image();
      im.onload = function(){ res({src:im, width:im.naturalWidth, height:im.naturalHeight, close:function(){ URL.revokeObjectURL(url); }}); };
      im.onerror = function(){ URL.revokeObjectURL(url); rej(new Error('decode')); };
      im.src = url;
    });
  }
  function sliceBlob(img, scale, W, y, h){
    return new Promise(function(res, rej){
      var c = document.createElement('canvas'); c.width = W; c.height = h;
      var ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, h);
      ctx.drawImage(img.src, 0, y / scale, img.width, h / scale, 0, 0, W, h);
      try { c.toBlob(function(b){ b ? res(b) : rej(new Error('blob')); }, 'image/jpeg', 0.9); } catch(e) { rej(e); }
    });
  }
  function readTicket(it){
    if (it.text) return readTextGroups(it, [{text: it.text, first: true, last: true}], function(){});
    var f = filesMem[it.id];
    if (isPdf(f)) return readPdf(it);
    if (!imgLimits) {
      it.status = 'error';
      it.msg = 'Slike ne mogu da se čitaju u ovom prikazu. Koristi PDF, ili kopiraj tekst sa slike (Google Lens ili Live Text) i nalepi ga u polje „Nalepi tekst tiketa“.';
      return Promise.resolve();
    }
    it.msg = 'pripremam sliku'; renderScan();
    return decodeImg(f).then(function(img){ return readImage(it, img); }, function(err){
      if (window.console) console.warn('decode failed, sending original', err);
      return readSlices(it, [function(){ return Promise.resolve(f); }], function(){}, 'screenshot');
    });
  }
  function evenSlices(total, maxH, ov){
    if (total <= maxH * 1.12) return [[0, total]];
    var cnt = Math.ceil((total - ov) / (maxH - ov)), sh = Math.ceil((total + (cnt - 1) * ov) / cnt), out = [];
    for (var j = 0; j < cnt; j++) { var st = j * (sh - ov); out.push([st, Math.min(sh, total - st)]); }
    return out;
  }
  function savedSigs(){ var m = {}; state.tickets.forEach(function(t){ m[sigOf(t.legs, t.stake)] = 1; }); return m; }
  function readImage(it, img){
    var W = Math.min(img.width, 1200), scale = W / img.width, H = Math.round(img.height * scale);
    var parts = evenSlices(H, Math.round(W * 1.3), Math.round(W * 0.12));
    var slices = parts.map(function(p){
      return function(){ return sliceBlob(img, scale, W, p[0], p[1]); };
    });
    var f = filesMem[it.id];
    return slices[0]().then(function(first){
      var used = false;
      slices[0] = function(){ if (!used) { used = true; return Promise.resolve(first); } return sliceBlob(img, scale, W, parts[0][0], parts[0][1]); };
      return readSlices(it, slices, function(){ img.close(); }, 'screenshot');
    }, function(err){
      if (window.console) console.warn('canvas slicing failed, sending original', err);
      img.close();
      return readSlices(it, [function(){ return Promise.resolve(f); }], function(){}, 'screenshot');
    });
  }
  function batchSize(){ return Math.max(1, Math.min(3, imgLimits && imgLimits.maxCount || 1)); }

  var PDFJS = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/';
  var pdfLibP = null;
  function loadScript(src){
    return new Promise(function(res, rej){ var el = document.createElement('script'); el.src = src; el.onload = res; el.onerror = function(){ rej(new Error('load')); }; document.head.appendChild(el); });
  }
  function loadPdfJs(){
    if (!pdfLibP) {
      pdfLibP = loadScript(PDFJS + 'pdf.min.js').then(function(){ return loadScript(PDFJS + 'pdf.worker.min.js'); }).then(function(){
        var lib = window.pdfjsLib; if (!lib) throw new Error('lib');
        lib.GlobalWorkerOptions.workerSrc = PDFJS + 'pdf.worker.min.js';
        return lib;
      });
      pdfLibP.catch(function(){ pdfLibP = null; });
    }
    return pdfLibP;
  }
  function isPdf(f){ return f && (f.type === 'application/pdf' || /\.pdf$/i.test(f.name || '')); }
  function readPdf(it){
    var f = filesMem[it.id], doc = null;
    it.msg = 'otvaram PDF'; renderScan();
    return loadPdfJs().then(function(lib){
      return f.arrayBuffer().then(function(buf){ return lib.getDocument({data: new Uint8Array(buf), isEvalSupported: false}).promise; });
    }).then(function(d){
      doc = d;
      var n = Math.min(doc.numPages, 40), pages = [];
      var chain = Promise.resolve();
      for (var i = 1; i <= n; i++) (function(k){ chain = chain.then(function(){ return doc.getPage(k).then(function(pg){ pages.push(pg); }); }); })(i);
      return chain.then(function(){
        it.msg = 'čitam tekst iz PDF-a'; renderScan();
        var texts = [], tchain = Promise.resolve();
        pages.forEach(function(pg){ tchain = tchain.then(function(){ return pg.getTextContent().then(function(tc){ texts.push(itemsToText(tc.items)); }, function(){ texts.push(''); }); }); });
        return tchain.then(function(){
          var total = texts.reduce(function(a, t){ return a + t.replace(/\s+/g, '').length; }, 0);
          if (total >= 150) {
            if (doc.numPages > 40) toast('PDF ima više od 40 strana, čita se samo prvih 40.');
            return readTextGroups(it, groupPages(texts), function(){ try { doc.destroy(); } catch(e) {} });
          }
          if (!imgLimits) { it.status = 'error'; it.msg = 'PDF ne sadrži tekst (verovatno je skeniran), a slike ne mogu da se čitaju u ovom prikazu.'; try { doc.destroy(); } catch(e) {} return; }
          return pdfAsImages();
        });
      });
      function pdfAsImages(){
        var W = 1200, ov = Math.round(W * 0.1), maxH = Math.round(W * 1.3);
        var slices = [], cache = {num: 0, canvas: null};
        pages.forEach(function(pg){
          var vp0 = pg.getViewport({scale: 1}), sc = W / vp0.width, vp = pg.getViewport({scale: sc}), pH = Math.round(vp.height);
          evenSlices(pH, maxH, ov).forEach(function(part){ (function(st, h){
            slices.push(function(){
              var ready = cache.num === pg.pageNumber ? Promise.resolve(cache.canvas) : (function(){
                var c = document.createElement('canvas'); c.width = W; c.height = pH;
                var ctx = c.getContext('2d'); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, pH);
                return pg.render({canvasContext: ctx, viewport: vp}).promise.then(function(){ cache.num = pg.pageNumber; cache.canvas = c; return c; });
              })();
              return ready.then(function(c){ return sliceBlob({src: c, width: W, height: pH}, 1, W, st, h); });
            });
          })(part[0], part[1]); });
        });
        if (doc.numPages > 40) toast('PDF ima više od 40 strana, čita se samo prvih 40.');
        return readSlices(it, slices, function(){ try { doc.destroy(); } catch(e) {} }, 'pdf');
      }
    }).catch(function(e){
      if (it.status === 'error') return;
      if (doc) { try { doc.destroy(); } catch(x) {} }
      it.status = 'error';
      if (window.console) console.error('PDF', e);
      it.msg = e && e.name === 'PasswordException' ? 'PDF je zaštićen lozinkom. Sačuvaj ga bez lozinke pa pokušaj ponovo.'
        : (e && e.message === 'load') || (e && e.message === 'lib') ? 'Alat za čitanje PDF-a nije učitan. Proveri internet vezu i pokušaj ponovo.'
        : 'PDF nije moguće otvoriti (' + esc(e && (e.name || e.message) || 'greška') + ').';
    });
  }

  function itemsToText(items){
    var rows = [];
    items.forEach(function(t){
      if (!t || typeof t.str !== 'string' || !t.transform) return;
      var y = t.transform[5], x = t.transform[4], row = null;
      for (var i = 0; i < rows.length; i++) { if (Math.abs(rows[i].y - y) < 3) { row = rows[i]; break; } }
      if (!row) { row = {y: y, parts: []}; rows.push(row); }
      row.parts.push({x: x, s: t.str});
    });
    rows.sort(function(a, b){ return b.y - a.y; });
    return rows.map(function(r){ r.parts.sort(function(a, b){ return a.x - b.x; }); return r.parts.map(function(p){ return p.s; }).join(' ').replace(/\s+/g, ' ').trim(); })
      .filter(function(l){ return l; }).join('\n');
  }
  function groupPages(texts){
    var LIM = 9000, groups = [], cur = [], len = 0;
    texts.forEach(function(t, i){
      var block = '=== strana ' + (i + 1) + ' ===\n' + t;
      if (cur.length && len + block.length > LIM) {
        groups.push(cur);
        var prev = cur[cur.length - 1];
        cur = prev.length < LIM / 2 ? [prev] : []; len = cur.length ? prev.length : 0;
      }
      cur.push(block); len += block.length;
    });
    if (cur.length) groups.push(cur);
    return groups.map(function(g, i){ return {text: g.join('\n\n').slice(0, 20000), first: i === 0, last: i === groups.length - 1}; });
  }
  function textPrompt(g){
    return 'The text below comes from a Serbian bookmaker (text extracted from a PDF, or copied from a website, app or photo) and contains one or more betting slips (tickets) ' +
      'with Euroleague basketball player prop bets on points, assists and rebounds. Text extraction can merge columns, split lines or shuffle their order: use the context ' +
      '(player name, market, line, odds, ticket number, stake) to rebuild each bet correctly. Keep each ticket separate and never merge bets from two tickets. ' +
      (g.first ? '' : 'The text can start in the middle of a ticket: skip a ticket whose bets begin before the text starts. ') +
      (g.last ? '' : 'The text can end in the middle of a ticket: skip a ticket whose bets continue past the end of the text. ') + '\n\n' +
      TERMS +
      'Reply with only compact JSON, no spaces or line breaks, in this exact shape:\n' +
      '{"t":[{"d":"2026-09-24","s":200,"o":45.3,"l":[["Hezonja","P","U",12.5,1.85],["Lessort","A","U",1.5,1.9]]}]}\n' +
      'Per ticket: d = date YYYY-MM-DD or null, s = stake or null, o = total odds or null, l = bets. ' +
      'Per bet: [player name, "P" points / "A" assists / "S" rebounds / "X" anything else, "U" under / "O" over, line, odds]. ' +
      'Use null for any value that is not in the text, never guess. If there is no complete ticket, reply {"t":[]}.' + knownTxt() +
      '\n\nTEXT:\n' + g.text;
  }
  function makeCollector(){
    var col = {seen: {}, saved: savedSigs(), found: [], skipped: 0};
    ui.queue.forEach(function(q){ if (q.ticket && q.ticket.legs) col.seen[sigOf(q.ticket.legs, q.ticket.stake)] = 1; });
    col.collect = function(r){
      var raw = Array.isArray(r) ? r : r && Array.isArray(r.t) ? r.t : r && Array.isArray(r.tickets) ? r.tickets : r && (Array.isArray(r.l) || Array.isArray(r.legs)) ? [r] : [];
      raw.forEach(function(tk){
        tk = tk && Array.isArray(tk.l) ? fromCompact(tk) : tk;
        if (!tk) return;
        var res = normalizeScan(tk);
        if (!res.ticket.legs.length) return;
        var sg = sigOf(res.ticket.legs, res.ticket.stake);
        if (col.seen[sg]) return;
        col.seen[sg] = 1;
        if (col.saved[sg]) { col.skipped++; return; }
        col.found.push(res);
      });
    };
    return col;
  }
  function errCode(e){ return e && e.code ? ' (kod: ' + e.code + (e.message ? ', ' + String(e.message).slice(0, 160) : '') + ')' : e && e.message ? ' (' + String(e.message).slice(0, 160) + ')' : ''; }
  function finishRead(it, col, failed, total, lastErr){
    if (col.found.length) {
      var idx = ui.queue.indexOf(it);
      var items = col.found.map(function(res, k){ return {id: uid(), name: it.name + ', tiket ' + (k + 1), status: 'done', msg: '', warn: res.warn, ticket: res.ticket}; });
      ui.queue.splice.apply(ui.queue, [idx < 0 ? ui.queue.length : idx, 0].concat(items));
    }
    if (failed.length) {
      it.status = 'error';
      it.msg = (col.found.length ? 'Pročitano ' + col.found.length + ' tiketa, ali ' : '') + 'delovi ' + failed.join(', ') + ' od ' + total + ' nisu pročitani' + errCode(lastErr) + '. Pokušaj ponovo, već pročitani tiketi se neće duplirati.';
      return;
    }
    if (!col.found.length) { it.status = 'error'; it.msg = col.skipped ? 'Svi tiketi iz ovog unosa su već sačuvani.' : 'Nisu pronađeni tiketi sa parovima.'; return; }
    ui.queue.splice(ui.queue.indexOf(it), 1);
    delete filesMem[it.id];
    toast('Pročitano tiketa: ' + col.found.length + (col.skipped ? ', već sačuvanih preskočeno: ' + col.skipped : '') + '.');
  }
  function readTextGroups(it, groups, cleanup){
    var col = makeCollector(), failed = [], lastErr = null, gi = 0;
    function next(){
      if (gi >= groups.length) return Promise.resolve();
      var label = gi + 1;
      it.msg = 'deo ' + label + ' od ' + groups.length + (col.found.length ? ', pronađeno ' + col.found.length : ''); renderScan();
      return sampleFn.json(textPrompt(groups[gi]), {modelTier: 'default'}).then(col.collect, function(e){
        if (e && FATAL.indexOf(e.code) >= 0) throw e;
        if (window.console) console.warn('Tekst deo ' + label, e);
        lastErr = e; failed.push(label);
      }).then(function(){ gi++; return next(); });
    }
    return next().then(function(){ cleanup(); finishRead(it, col, failed, groups.length, lastErr); }, function(e){
      cleanup();
      finishRead(it, col, [], groups.length, null);
      scanErr(it, e);
      if (col.found.length) it.msg = 'Pročitano ' + col.found.length + ' tiketa pre prekida. ' + it.msg;
    });
  }
  var FATAL = ['not_granted','sampling_disabled','not_declared','capability_disabled','capability_removed','images_unavailable','session_expired','rate_limited','cancelled'];
  function readSlices(it, slices, cleanup, kind){
    var m = batchSize(), batches = [];
    if (m > 1 && slices.length > 1) { for (var i = 0; ; i += m - 1) { batches.push(slices.slice(i, i + m)); if (i + m >= slices.length) break; } }
    else slices.forEach(function(sl){ batches.push([sl]); });
    var seen = {}, saved = savedSigs(), found = [], skipped = 0, failed = [], lastErr = null;
    ui.queue.forEach(function(q){ if (q.ticket && q.ticket.legs) seen[sigOf(q.ticket.legs, q.ticket.stake)] = 1; });
    function collect(r){
      var raw = Array.isArray(r) ? r : r && Array.isArray(r.t) ? r.t : r && Array.isArray(r.tickets) ? r.tickets : r && (Array.isArray(r.l) || Array.isArray(r.legs)) ? [r] : [];
      var list = raw.map(function(tk){ return tk && Array.isArray(tk.l) ? fromCompact(tk) : tk; });
      list.forEach(function(tk){
        if (!tk) return;
        var res = normalizeScan(tk);
        if (!res.ticket.legs.length) return;
        var sg = sigOf(res.ticket.legs, res.ticket.stake);
        if (seen[sg]) return;
        seen[sg] = 1;
        if (saved[sg]) { skipped++; return; }
        found.push(res);
      });
    }
    function run(parts){
      var blobs = [], chain = Promise.resolve();
      parts.forEach(function(make){ chain = chain.then(function(){ return make().then(function(bl){ blobs.push(bl); }); }); });
      return chain.then(function(){ return sampleFn.json(longPrompt(blobs.length, kind), {images: blobs, modelTier: 'default'}); }).then(collect);
    }
    function isFatal(e){ return e && FATAL.indexOf(e.code) >= 0; }
    var bi = 0;
    function next(){
      if (bi >= batches.length) return Promise.resolve();
      var label = bi + 1;
      it.msg = 'deo ' + label + ' od ' + batches.length + (found.length ? ', pronađeno ' + found.length : ''); renderScan();
      var b = batches[bi];
      return run(b).catch(function(e){
        if (isFatal(e)) throw e;
        if (window.console) console.warn('Deo ' + label, e);
        lastErr = e;
        if (b.length < 2) { failed.push(label); return; }
        var chain = Promise.resolve();
        b.forEach(function(one){
          chain = chain.then(function(){ return run([one]).catch(function(e2){ if (isFatal(e2)) throw e2; lastErr = e2; if (failed.indexOf(label) < 0) failed.push(label); }); });
        });
        return chain;
      }).then(function(){ bi++; return next(); });
    }
    function addFound(){
      if (!found.length) return;
      var idx = ui.queue.indexOf(it);
      var items = found.map(function(res, k){ return {id: uid(), name: it.name + ', tiket ' + (k + 1), status: 'done', msg: '', warn: res.warn, ticket: res.ticket}; });
      ui.queue.splice.apply(ui.queue, [idx < 0 ? ui.queue.length : idx, 0].concat(items));
    }
    function code(e){ return e && e.code ? ' (kod: ' + e.code + (e.message ? ', ' + String(e.message).slice(0, 160) : '') + ')' : e && e.message ? ' (' + String(e.message).slice(0, 160) + ')' : ''; }
    return next().then(function(){
      cleanup();
      addFound();
      if (failed.length) {
        it.status = 'error';
        it.msg = (found.length ? 'Pročitano ' + found.length + ' tiketa, ali ' : '') + 'delovi ' + failed.join(', ') + ' od ' + batches.length + ' nisu pročitani' + code(lastErr) + '. Pokušaj ponovo, već pročitani tiketi se neće duplirati.';
        return;
      }
      if (!found.length) { it.status = 'error'; it.msg = skipped ? 'Svi tiketi iz ovog fajla su već sačuvani.' : 'U fajlu nisu pronađeni tiketi.'; return; }
      ui.queue.splice(ui.queue.indexOf(it), 1);
      delete filesMem[it.id];
      toast('Pročitano tiketa: ' + found.length + (skipped ? ', već sačuvanih preskočeno: ' + skipped : '') + '.');
    }, function(e){
      cleanup();
      addFound();
      if (e && e.code) scanErr(it, e);
      else { it.status = 'error'; it.msg = 'Fajl nije moguće obraditi' + code(e) + '.'; }
      if (found.length) it.msg = 'Pročitano ' + found.length + ' tiketa pre prekida. ' + it.msg;
    });
  }
  function scanErr(it, e){
      var c = e && e.code, stopAll = false;
      it.status = 'error';
      if (['not_granted','sampling_disabled','not_declared','capability_disabled','capability_removed','images_unavailable','session_expired'].indexOf(c) >= 0) {
        it.msg = c === 'session_expired' ? 'Prijavi se ponovo na Claude pa pokušaj.' : 'Čitanje slika nije dostupno u ovom prikazu.'; stopAll = true;
        if (c === 'images_unavailable') { imgLimits = null; scanState = 'noimages'; it.msg = 'Slike ne mogu da se čitaju u ovom prikazu. Koristi PDF ili nalepi tekst tiketa.'; stopAll = false; }
        else if (c !== 'session_expired') { sampleFn = null; scanState = 'denied'; }
      } else if (c === 'rate_limited') { it.msg = 'Previše zahteva zaredom. Sačekaj malo pa pokušaj ponovo.'; stopAll = true; }
      else if (c === 'image_rejected') it.msg = 'Slika nije prihvaćena. Probaj drugu sliku.';
      else if (c === 'refused') it.msg = 'Ova slika nije obrađena. Probaj drugu sliku.';
      else if (c === 'cancelled') it.msg = 'Prekinuto.';
      else it.msg = 'Tiket nije pročitan (kod: ' + (c || 'nepoznat') + (e && e.message ? ', ' + String(e.message).slice(0, 160) : '') + '). Pokušaj ponovo.';
      if (stopAll) ui.queue.forEach(function(q){ if (q.status === 'waiting') { q.status = 'error'; q.msg = it.msg; } });
  }
  function scanHtml(){
    var note = scanState === 'checking' ? 'Proveravam da li je čitanje slika dostupno…'
      : scanState === 'nosample' ? 'Čitanje slika nije dostupno u ovom prikazu. Otvori aplikaciju preko linka na claude.ai, ulogovan na svoj nalog, pa osveži stranicu.'
      : scanState === 'noimages' || (scanState === 'ok' && !imgLimits) ? 'U ovom prikazu slike ne mogu da se čitaju, ali PDF i nalepljen tekst rade. Slike možda rade ako aplikaciju otvoriš na drugom uređaju ili u browseru na claude.ai.'
      : scanState === 'denied' ? 'Čitanje slika nije odobreno. Osveži stranicu i dozvoli pristup kad se pojavi pitanje.' : '';
    var ready = ui.queue.filter(function(q){ return q.status === 'done' && !q.warn.length; }).length;
    var items = ui.queue.map(function(q){
      var info, acts = '';
      if (q.status === 'waiting') info = '<span class="tag pending">Čeka</span>';
      else if (q.status === 'working') info = '<span class="tag pending">Čitam…</span>' + (q.msg ? ' ' + esc(q.msg) : '');
      else if (q.status === 'done') {
        var t = q.ticket, odds = t.legs.reduce(function(a, l){ return a * num(l.odds); }, 1);
        info = '<span class="tag ' + (q.warn.length ? 'neutral' : 'hit') + '">' + (q.warn.length ? 'Proveri' : 'Spreman') + '</span> ' + parova(t.legs.length) + ', kvota ' + fmt(odds) + (t.stake ? ', ulog ' + fmt(num(t.stake)) : '') +
          (q.warn.length ? '<ul>' + q.warn.map(function(w){ return '<li>' + esc(w) + '</li>'; }).join('') + '</ul>' : '');
        acts = '<button class="btn sm" data-act="scanOpen" data-id="' + q.id + '">Otvori u formi</button>';
      } else {
        info = '<span class="tag miss">Greška</span> ' + esc(q.msg);
        if ((filesMem[q.id] || q.text) && sampleFn) acts = '<button class="btn sm" data-act="scanRetry" data-id="' + q.id + '">Pokušaj ponovo</button>';
      }
      if (q.status !== 'working') acts += '<button class="btn sm" data-act="scanDel" data-id="' + q.id + '">Ukloni</button>';
      return '<div class="q"><div><div class="name">' + esc(q.name) + '</div><div>' + info + '</div></div><div class="acts">' + acts + '</div></div>';
    }).join('');
    return '<div class="scan"><div class="scan-h"><div><b>Automatski unos tiketa</b><p class="hint">' + (imgLimits ? 'Izaberi slike ili PDF sa tiketima, može više odjednom. ' : 'Izaberi PDF sa tiketima ili nalepi tekst tiketa. ') + 'Kolo, i ulog ako se ne vidi, uzimaju se iz polja iznad.</p>' + (note ? '<p class="hint" style="color:var(--pend)">' + note + '</p>' : '') + '</div>' +
      (sampleFn ? '<div class="acts" style="display:flex;gap:6px;flex-wrap:wrap"><button class="btn primary" data-act="pickScan">' + (imgLimits ? 'Izaberi slike ili PDF' : 'Izaberi PDF') + '</button><button class="btn' + (ui.pasteTxt ? ' on' : '') + '" data-act="togglePasteTxt">Nalepi tekst tiketa</button></div><input type="file" id="scanInput" accept="' + esc((imgLimits ? imgLimits.mediaTypes : []).concat(['application/pdf','.pdf']).join(',')) + '" multiple hidden>' : '') +
      '</div>' +
      (sampleFn && ui.pasteTxt ? '<div style="margin-top:10px"><p class="hint">Nalepi tekst tiketa u bilo kom obliku: kopiran sa sajta kladionice, iz PDF-a, ili sa slike. Na iPhone-u tekst sa slike kopiraš preko Live Text (dugo držiš prst na tekstu u Photos), a na Androidu preko Google Lens opcije Tekst. Može više tiketa odjednom.</p><textarea id="pasteTxtBox" placeholder="Nalepi tekst ovde"></textarea><div class="btns"><button class="btn primary" data-act="readPasteTxt">Pročitaj tekst</button></div></div>' : '') +
      items + diagHtml() +
      (ui.queue.length ? '<div class="btns"><button class="btn primary" data-act="scanSaveAll"' + (ready && !busy ? '' : ' disabled') + '>' + (busy ? 'Čuvam…' : 'Sačuvaj spremne tikete (' + ready + ')') + '</button><button class="btn" data-act="scanClear">Očisti listu</button></div>' : '') +
      '<div class="btns"><button class="btn sm" data-act="scanDiag"' + (diag && diag.running ? ' disabled' : '') + '>Proveri čitanje</button></div>' +
    '</div>';
  }
  var diag = null;
  function runDiag(){
    if (diag && diag.running) return;
    diag = {running: true, steps: []};
    function step(name, p){
      var st = {name: name, res: '…'}; diag.steps.push(st); renderScan();
      return Promise.resolve().then(p).then(function(v){ st.res = 'u redu' + (v ? ': ' + v : ''); st.ok = true; renderScan(); return true; },
        function(e){ st.res = 'greška: ' + (e && e.code ? e.code + ' ' : '') + String(e && e.message || e || '').slice(0, 200); st.ok = false; renderScan(); return false; });
    }
    step('Pristup Claude-u', function(){ return sampleP.then(function(fn){ if (!fn) throw new Error('nije dostupan u ovom prikazu'); sampleFn = sampleFn || fn; return 'da'; }); })
    .then(function(){ return step('Tekstualni zahtev', function(){ return sampleFn.json('Reply with only this JSON: {"ok":true}', {modelTier: 'quick', cache: false}).then(function(r){ if (!r || r.ok !== true) throw new Error('neočekivan odgovor'); return 'radi'; }); }); })
    .then(function(){ return step('Čitanje slika', function(){ return sampleFn.limits().then(function(l){ return l && l.images ? 'dostupno' : 'nije dostupno u ovom prikazu (PDF i tekst i dalje rade)'; }); }); })
    .then(function(){
      var q = ui.queue.filter(function(x){ return filesMem[x.id] && isPdf(filesMem[x.id]); })[0];
      if (!q) { diag.steps.push({name: 'PDF', res: 'dodaj PDF, pa ponovo klikni „Proveri čitanje“', ok: null}); renderScan(); return; }
      var f = filesMem[q.id], lib = null, doc = null;
      return step('Učitavanje PDF alata', function(){ return loadPdfJs().then(function(l){ lib = l; return 'verzija ' + (l.version || '?'); }); })
      .then(function(ok){ if (!ok) return; return step('Otvaranje PDF-a (' + q.name + ', ' + Math.round(f.size / 1024) + ' KB)', function(){
        return f.arrayBuffer().then(function(buf){ return lib.getDocument({data: new Uint8Array(buf), isEvalSupported: false}).promise; }).then(function(d){ doc = d; return 'strana: ' + d.numPages; });
      }); })
      .then(function(ok){ if (!ok) return; return step('Tekst iz PDF-a', function(){
        var n = Math.min(doc.numPages, 3), out = [], ch = Promise.resolve();
        for (var k = 1; k <= n; k++) (function(k){ ch = ch.then(function(){ return doc.getPage(k).then(function(pg){ return pg.getTextContent(); }).then(function(tc){ out.push(itemsToText(tc.items)); }); }); })(k);
        return ch.then(function(){
          var t = out.join('\n'), chars = t.replace(/\s+/g, '').length;
          try { doc.destroy(); } catch(e) {}
          if (chars < 50) throw new Error('prve ' + n + ' strane skoro bez teksta (' + chars + ' znakova), PDF je verovatno skeniran');
          return chars + ' znakova na prve ' + n + ' strane. Početak: ' + t.replace(/\s+/g, ' ').slice(0, 140);
        });
      }); });
    })
    .then(function(){ diag.running = false; renderScan(); });
  }
  function diagHtml(){
    if (!diag) return '';
    return '<div class="q" style="grid-template-columns:1fr"><div><b>Provera</b>' + diag.steps.map(function(st){
      return '<div style="font-size:13px;margin-top:4px"><span class="tag ' + (st.ok === true ? 'hit' : st.ok === false ? 'miss' : 'pending') + '">' + esc(st.name) + '</span> ' + esc(st.res) + '</div>';
    }).join('') + (diag.running ? '' : '<p class="hint" style="margin-top:6px">Pošalji ovaj rezultat u razgovoru sa Claude-om.</p>') + '</div></div>';
  }
  function renderScan(){ var b = $('#scanBox'); if (b) b.innerHTML = scanHtml(); }
  function saveAllScanned(){
    if (running) { toast('Sačekaj da se završi čitanje.'); return; }
    var ok = ui.queue.filter(function(q){ return q.status === 'done' && !q.warn.length; });
    if (!ok.length) { toast('Nema tiketa spremnih za čuvanje.'); return; }
    var round = String(ui.draft.round).trim(), defStake = num(ui.draft.stake);
    if (!round) { ui.err = 'Upiši kolo u polje iznad, pa sačuvaj ponovo.'; render(); return; }
    var missing = ok.filter(function(q){ return !num(q.ticket.stake); }).length;
    if (missing && !(defStake > 0)) { ui.err = 'Na ' + missing + ' tiketa se ne vidi ulog. Upiši ulog u polje iznad, pa sačuvaj ponovo.'; render(); return; }
    ui.err = '';
    var ns = clone(state);
    ok.forEach(function(q){
      var t = q.ticket;
      ns.tickets.push({id: uid(), date: t.date, round: round, stake: num(t.stake) || defStake, legs: t.legs.map(function(l){ return {p:l.p, team:l.team, stat:l.stat, line:num(l.line), odds:num(l.odds)}; })});
      t.legs.forEach(function(l){ if (l.team) ns.players[l.p] = l.team; else if (!(l.p in ns.players)) ns.players[l.p] = ''; });
    });
    ui.pendingQ = ok.map(function(q){ return q.id; });
    save(ns, ok.length === 1 ? 'Tiket sačuvan.' : 'Sačuvano tiketa: ' + ok.length + '.', function(){
      ui.queue = ui.queue.filter(function(q){ return ui.pendingQ.indexOf(q.id) < 0; }); ui.pendingQ = [];
    });
  }

  function loadLocal(){
    try {
      var l = JSON.parse(localStorage.getItem('mt-state') || 'null');
      if (l && Array.isArray(l.tickets) && (l.savedAt || 0) > (state.savedAt || 0)) {
        state = l; state.results = state.results || {}; state.players = state.players || {};
      }
    } catch(e) {}
  }
  function saveLocal(s){ try { localStorage.setItem('mt-state', JSON.stringify(s)); return true; } catch(e) { return false; } }

  function buildDoc(s){
    var css = $('#css').textContent;
    var app = $('#app').textContent;
    var json = JSON.stringify(s).replace(/</g, '\\u003c');
    return '<!doctype html>\n<html lang="sr">\n<head>\n' + HEAD + '\n<style id="css">' + css + '</style>\n</head>\n<body>\n' +
      '<div id="root"><div class="wrap"><p class="hint">Učitavanje…</p></div></div>\n' +
      '<' + SC + ' type="application/json" id="state">' + json + '</' + SC + '>\n' +
      '<' + SC + ' id="app">' + app + '</' + SC + '>\n</body>\n</html>\n';
  }

  function save(ns, msg, onDone){
    if (busy) return;
    if (running && mode === 'artifact') { toast('Sačekaj da se završi čitanje tiketa sa slika, pa sačuvaj.'); return; }
    ns.savedAt = Date.now();
    busy = true; render();
    capP.then(function(art){
      if (art && mode === 'artifact') {
        try {
          sessionStorage.setItem('mt-ui', JSON.stringify(ui));
          sessionStorage.setItem('mt-pending', String(ns.savedAt));
          sessionStorage.setItem('mt-flash', msg);
        } catch(e) {}
        var attempt = function(retried){
          art.publish(buildDoc(ns)).then(function(){
            /* the view reloads to the new version */
          }, function(e){
            var code = e && e.code;
            if (code === 'conflict') { return; }
            if (code === 'upstream_error' && !retried) { setTimeout(function(){ attempt(true); }, 800 + Math.random() * 800); return; }
            try { sessionStorage.removeItem('mt-pending'); } catch(x) {}
            busy = false;
            if (['not_writer','not_granted','not_declared','consent_required','capability_disabled','capability_removed'].indexOf(code) >= 0) {
              mode = 'readonly';
              toast('Ova verzija je samo za čitanje. Izmene nisu sačuvane.');
            } else if (code === 'rate_limited') {
              toast('Previše čuvanja zaredom. Sačekaj malo pa sačuvaj ponovo.');
            } else if (code === 'too_large') {
              toast('Podaci su preveliki za čuvanje. Izvezi rezervnu kopiju i obriši stare tikete.');
            } else {
              toast('Čuvanje nije uspelo (' + (code || 'greška') + '). Pokušaj ponovo.');
            }
            render();
          });
        };
        attempt(false);
      } else if (mode === 'readonly') {
        busy = false; toast('Ova verzija je samo za čitanje.'); render();
      } else {
        busy = false;
        if (saveLocal(ns)) { state = ns; if (onDone) onDone(); toast(msg); }
        else toast('Čuvanje u browseru nije uspelo.');
        saveUi(); render();
      }
    });
  }

  var toastTimer;
  function toast(m){
    var t = $('.toast'); if (!t) { t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role','status'); document.body.appendChild(t); }
    t.textContent = m; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(function(){ t.hidden = true; }, 3500);
  }

  /* ---------- calculations ---------- */
  function keyOf(t, l){ return [String(t.round).trim(), l.p.trim().toLowerCase(), l.stat, l.line].join('|'); }
  function statusFrom(r, line){
    if (!r) return 'pending';
    if (r.dnp) return 'void';
    if (r.actual == null) return r.outcome === 'hit' || r.outcome === 'miss' || r.outcome === 'void' ? r.outcome : 'pending';
    if (r.actual < line) return 'hit';
    if (r.actual > line) return 'miss';
    return 'void';
  }
  function legStatus(t, l){ return statusFrom(state.results[keyOf(t, l)], l.line); }
  function admBonusPct(n){ var T = {4: 0.03, 5: 0.05, 6: 0.07, 7: 0.11, 8: 0.16, 9: 0.21, 10: 0.26}; return n > 10 ? 0.26 + 0.05 * (n - 10) : (T[n] || 0); }
  function ticketInfo(t){
    var st = 'won', odds = 1, all = 1, nv = 0;
    t.legs.forEach(function(l){
      var s = legStatus(t, l);
      all *= l.odds;
      if (s === 'miss') st = 'lost';
      else if (s === 'pending' && st !== 'lost') st = 'pending';
      if (s !== 'void') { odds *= l.odds; nv++; }
    });
    var bonus = t.bonus != null ? t.bonus : t.stake * odds * admBonusPct(nv);
    return {st: st, odds: st === 'won' ? odds : all, payout: st === 'won' ? t.stake * odds + bonus : (st === 'lost' ? (t.refund || 0) : 0)};
  }
  function roundDays(){
    var m = {}, out = {};
    state.tickets.forEach(function(t){ var r = String(t.round); (m[r] = m[r] || {})[t.date || ''] = 1; });
    Object.keys(m).forEach(function(r){ out[r] = Object.keys(m[r]).sort(); });
    return out;
  }
  function dayOf(t, RD){ var d = (RD || roundDays())[String(t.round)] || []; return d.indexOf(t.date || '') + 1; }
  function inScope(t, RD){
    var sc = ui.scope || 'all'; if (sc === 'all') return true;
    var q = sc.split(':'); if (String(t.round) !== q[1]) return false;
    return q[2] ? String(dayOf(t, RD)) === q[2] : true;
  }
  function scopedTickets(){ var RD = roundDays(); return state.tickets.filter(function(t){ return inScope(t, RD); }); }
  function fmtDate(d){ var q = String(d || '').split('-'); return q.length === 3 ? (+q[2]) + '.' + (+q[1]) + '.' : d; }
  function scopeLabel(sc){
    if (!sc || sc === 'all') return 'Sva kola';
    var q = sc.split(':'), RD = roundDays();
    if (!q[2]) return 'Kolo ' + q[1] + ((RD[q[1]] || []).length > 1 ? ', oba dana' : '');
    return 'Kolo ' + q[1] + ', dan ' + q[2] + ' (' + fmtDate((RD[q[1]] || [])[+q[2] - 1]) + ')';
  }
  function scopeOptions(){
    var RD = roundDays(), opts = ['all'];
    rounds().forEach(function(r){ opts.push('r:' + r); if ((RD[r] || []).length > 1) RD[r].forEach(function(d, i){ opts.push('r:' + r + ':' + (i + 1)); }); });
    return opts;
  }
  function picks(all){
    var m = {}, order = [], RD = roundDays();
    (all ? state.tickets : state.tickets.filter(function(t){ return inScope(t, RD); })).forEach(function(t){
      t.legs.forEach(function(l){
        var k = keyOf(t, l);
        if (!m[k]) { m[k] = {k:k, round:String(t.round), day: dayOf(t, RD), date: t.date, p:l.p, team:l.team, stat:l.stat, line:l.line, oddsSum:0, count:0, r:state.results[k] || null, status:legStatus(t, l)}; order.push(k); }
        m[k].oddsSum += l.odds; m[k].count++;
        if (!m[k].team && l.team) m[k].team = l.team;
        if (m[k].sc == null && l.sc != null) m[k].sc = l.sc;
      });
    });
    return order.map(function(k){ var e = m[k]; e.avgOdds = e.oddsSum / e.count; return e; });
  }
  function settledPicks(all){ return picks(all).filter(function(e){ return e.status === 'hit' || e.status === 'miss'; }); }
  function group(list, fn){
    var g = {}, order = [];
    list.forEach(function(e){
      var lab = fn(e); if (lab == null || lab === '') return;
      var k = String(lab).toLowerCase();
      if (!g[k]) { g[k] = {k:lab, n:0, h:0, be:0}; order.push(k); }
      g[k].n++; if (e.status === 'hit') g[k].h++; g[k].be += 1 / e.avgOdds;
    });
    return order.map(function(k){ var x = g[k]; x.rate = x.h / x.n; x.be = x.be / x.n; return x; });
  }
  function verdict(x){
    if (x.n < 5) return ['malo', 'Malo podataka'];
    if (x.rate >= x.be + 0.05) return ['dobro', 'Prolazi'];
    if (x.rate < x.be - 0.05) return ['lose', 'Igraj manje'];
    return ['neutral', 'Oko nule'];
  }
  function spreadBucket(e){
    var s = e.r && e.r.spread;
    if (s == null) return 'Bez podatka';
    if (s <= -12) return 'Tim veliki favorit (−12 i više)';
    if (s <= -6) return 'Tim favorit (−6 do −11,5)';
    if (s < 6) return 'Izjednačeno (do ±5,5)';
    return 'Tim autsajder (+6 i više)';
  }
  function summary(){
    var list = scopedTickets();
    var o = {staked:0, ret:0, pend:0, won:0, settled:0, total:list.length, fresh:0, reinv:0};
    list.forEach(function(t){
      var i = ticketInfo(t);
      var frA = t.freshAmt != null ? t.freshAmt : (t.fund === 'dobitak' ? 0 : t.stake); o.fresh += frA; o.reinv += t.stake - frA;
      if (i.st === 'pending') { o.pend += t.stake; return; }
      o.settled++; o.staked += t.stake; o.ret += i.payout; if (i.st === 'won') o.won++;
    });
    o.profit = o.ret - o.staked; o.roi = o.staked ? o.profit / o.staked : null;
    o.left = o.ret - o.reinv; o.roiOwn = o.fresh ? o.profit / o.fresh : null;
    var sp = settledPicks();
    o.pn = sp.length; o.ph = sp.filter(function(e){ return e.status === 'hit'; }).length;
    o.prate = sp.length ? o.ph / sp.length : null;
    o.be = sp.length ? sp.reduce(function(a, e){ return a + 1 / e.avgOdds; }, 0) / sp.length : null;
    return o;
  }
  function rounds(){
    var seen = {}, list = [];
    state.tickets.forEach(function(t){ var r = String(t.round); if (!seen[r]) { seen[r] = 1; list.push(r); } });
    return list.sort(function(a, b){ var x = parseFloat(a), y = parseFloat(b); if (isFinite(x) && isFinite(y)) return x - y; return a.localeCompare(b); });
  }

  /* ---------- views ---------- */
  function header(){
    var s = summary();
    var saveTxt = mode === 'artifact' ? 'Podaci se čuvaju u ovoj stranici' : mode === 'local' ? 'Podaci se čuvaju samo u ovom browseru' : mode === 'readonly' ? 'Samo za čitanje' : 'Povezivanje…';
    var cls = s.profit > 0 ? 'pos' : s.profit < 0 ? 'neg' : '';
    return '<header class="slip">' +
      '<div class="slip-top"><h1>Evroliga minusi</h1><span class="save-state">' + saveTxt + '</span></div>' +
      (state.tickets.length ? '<div class="filters" style="margin:-4px 0 12px"><label class="f" style="flex-direction:row;align-items:center;gap:8px">Prikaz <select data-act="scope" style="width:auto">' + scopeOptions().map(function(o){ return '<option value="' + esc(o) + '"' + ((ui.scope || 'all') === o ? ' selected' : '') + '>' + esc(scopeLabel(o)) + '</option>'; }).join('') + '</select></label><span class="hint" style="margin:0">Važi za zbir gore, karticu Tiketi i Analizu.</span></div>' : '') +
      '<div class="slip-main">' +
        '<div class="bal"><div class="lbl">Bilans završenih tiketa</div><div class="big num ' + cls + '">' + signed(s.profit) + '</div>' +
        '<div class="sub">Povraćaj ' + (s.roi == null ? '–' : (s.roi > 0 ? '+' : '') + pct(s.roi)) + ' na sve uloženo' + (s.reinv && s.roiOwn != null ? ', ' + (s.roiOwn > 0 ? '+' : '') + pct(s.roiOwn) + ' na svoj novac' : '') + '</div></div>' +
        '<dl class="facts">' +
          '<div><dt>Uloženo</dt><dd>' + fmt(s.staked) + '</dd></div>' +
          '<div><dt>Svoj novac</dt><dd>' + fmt(s.fresh) + '</dd></div>' +
          '<div><dt>Igrano iz dobitka</dt><dd>' + fmt(s.reinv) + (s.reinv && (ui.scope || 'all') === 'all' ? ' <small>od dobitka ostalo ' + fmt(Math.max(0, s.left)) + '</small>' : '') + '</dd></div>' +
          '<div><dt>Vraćeno</dt><dd>' + fmt(s.ret) + '</dd></div>' +
          '<div><dt>Dobitni tiketi</dt><dd>' + s.won + ' <small>od ' + s.settled + '</small></dd></div>' +
          '<div><dt>U igri</dt><dd>' + fmt(s.pend) + ' <small>' + (s.total - s.settled) + ' tiketa</small></dd></div>' +
          '<div><dt>Pogođeni parovi</dt><dd>' + pct(s.prate) + '</dd></div>' +
        '</dl>' +
      '</div></header>';
  }
  function tabs(){
    var pend = picks(true).filter(function(e){ return e.status === 'pending'; }).length;
    var t = [['novi','Novi tiket',''],['rezultati','Unos rezultata', pend ? String(pend) : ''],['tiketi','Tiketi', String(state.tickets.length)],['analiza','Analiza',''],['generator','Generator','']];
    return '<nav class="tabs" role="tablist">' + t.map(function(x){
      return '<button role="tab" data-act="tab" data-v="' + x[0] + '" aria-selected="' + (ui.tab === x[0]) + '">' + x[1] + (x[2] ? '<span class="count">' + x[2] + '</span>' : '') + '</button>';
    }).join('') + '</nav>';
  }
  function datalists(){
    var names = Object.keys(state.players);
    state.tickets.forEach(function(t){ t.legs.forEach(function(l){ if (names.indexOf(l.p) < 0) names.push(l.p); }); });
    var teams = [];
    Object.keys(state.players).forEach(function(k){ var v = state.players[k]; if (v && teams.indexOf(v) < 0) teams.push(v); });
    return '<datalist id="dl-p">' + names.sort().map(function(n){ return '<option value="' + esc(n) + '">'; }).join('') + '</datalist>' +
           '<datalist id="dl-t">' + teams.sort().map(function(n){ return '<option value="' + esc(n) + '">'; }).join('') + '</datalist>';
  }
  function draftCalc(){
    var d = ui.draft, odds = 1, n = 0;
    d.legs.forEach(function(l){ var o = num(l.odds); if (l.p.trim() && o) { odds *= o; n++; } });
    var st = num(d.stake);
    return '<div><span>Parova</span><b class="num">' + n + '</b></div>' +
           '<div><span>Ukupna kvota</span><b class="num">' + (n ? fmt(odds) : '–') + '</b></div>' +
           '<div><span>Mogući dobitak</span><b class="num">' + (n && st ? fmt(odds * st) : '–') + '</b></div>';
  }
  function viewNew(){
    var d = ui.draft;
    var legs = d.legs.map(function(l, i){
      return '<div class="leg">' +
        '<div class="c-p"><input type="text" list="dl-p" placeholder="Igrač" aria-label="Igrač ' + (i + 1) + '" data-lf="p" data-i="' + i + '" value="' + esc(l.p) + '"></div>' +
        '<div><input type="text" list="dl-t" placeholder="Tim" aria-label="Tim" data-lf="team" data-i="' + i + '" value="' + esc(l.team) + '"></div>' +
        '<div><select aria-label="Statistika" data-lf="stat" data-i="' + i + '">' + ['P','A','S'].map(function(s){ return '<option value="' + s + '"' + (l.stat === s ? ' selected' : '') + '>' + STAT[s] + '</option>'; }).join('') + '</select></div>' +
        '<div><input type="text" inputmode="decimal" placeholder="Linija" aria-label="Linija" data-lf="line" data-i="' + i + '" value="' + esc(l.line) + '"></div>' +
        '<div><input type="text" inputmode="decimal" placeholder="Kvota" aria-label="Kvota" data-lf="odds" data-i="' + i + '" value="' + esc(l.odds) + '"></div>' +
        '<div class="c-x"><button class="x" title="Ukloni par" aria-label="Ukloni par ' + (i + 1) + '" data-act="delLeg" data-i="' + i + '">×</button></div>' +
      '</div>';
    }).join('');
    return '<section class="panel">' +
      '<div class="row3">' +
        '<label class="f">Datum<input type="date" data-f="date" value="' + esc(d.date) + '"></label>' +
        '<label class="f">Kolo<input type="text" data-f="round" placeholder="npr. 7" value="' + esc(d.round) + '"></label>' +
        '<label class="f">Ulog<input type="text" inputmode="decimal" data-f="stake" placeholder="npr. 200" value="' + esc(d.stake) + '"></label>' +
        '<label class="f">Novac<select data-f="fund"><option value="novi"' + (d.fund !== 'dobitak' ? ' selected' : '') + '>Svež novac</option><option value="dobitak"' + (d.fund === 'dobitak' ? ' selected' : '') + '>Iz dobitka</option></select></label>' +
      '</div>' +
      '<div id="scanBox">' + scanHtml() + '</div>' +
      '<div class="legs-head"><span>Igrač</span><span>Tim</span><span>Statistika</span><span>Linija (minus)</span><span>Kvota</span><span></span></div>' +
      legs +
      '<div class="btns">' +
        '<button class="btn" data-act="addLeg">Dodaj par</button>' +
        '<button class="btn" data-act="copyLast"' + (state.tickets.length ? '' : ' disabled') + '>Kopiraj poslednji tiket</button>' +
        '<button class="btn' + (ui.paste ? ' on' : '') + '" data-act="togglePaste">Nalepi listu parova</button>' +
      '</div>' +
      (ui.paste ? '<div style="margin-top:12px"><p class="hint">Jedan par po redu: igrač; statistika (P, A ili S); linija; kvota; tim (tim nije obavezan). Radi i sa tabom ili razmakom, npr. <code>Hezonja P 12.5 1.85</code>.</p>' +
        '<textarea id="pasteBox" placeholder="Hezonja; P; 12.5; 1.85; Real"></textarea><div class="btns"><button class="btn" data-act="doPaste">Ubaci parove</button></div></div>' : '') +
      '<div class="calc" id="calc">' + draftCalc() + '</div>' +
      (ui.err ? '<div class="err" role="alert">' + esc(ui.err) + '</div>' : '') +
      '<div class="btns"><button class="btn primary" data-act="saveTicket"' + (busy ? ' disabled' : '') + '>' + (busy ? 'Čuvam…' : 'Sačuvaj tiket') + '</button></div>' +
    '</section>' + datalists();
  }

  function resValue(e){
    var d = ui.resDraft[e.k];
    if (d) return d;
    var r = e.r || {};
    return {actual: r.actual == null ? '' : String(r.actual), dnp: !!r.dnp, spread: r.spread == null ? '' : String(r.spread), blowout: !!r.blowout, outcome: r.outcome || ''};
  }
  function draftStatus(v, line){ return statusFrom({actual: num(v.actual), dnp: v.dnp, outcome: v.outcome}, line); }
  var STATUS_TXT = {hit:'Prošao', miss:'Pao', void:'Vraćen', pending:'Čeka'};
  function viewResults(){
    var rs = rounds();
    if (!rs.length) return '<section class="panel empty">Nema tiketa. Prvo unesi tiket, pa ovde upiši kako su igrači odigrali.<br><button class="btn" data-act="tab" data-v="novi">Unesi tiket</button></section>';
    var RD = roundDays(), ropts = [];
    rs.forEach(function(r){ ropts.push(r); if ((RD[r] || []).length > 1) RD[r].forEach(function(d, i){ ropts.push(r + ':' + (i + 1)); }); });
    if (ropts.indexOf(ui.resRound) < 0) ui.resRound = rs[rs.length - 1];
    var rq = String(ui.resRound).split(':');
    var list = picks(true).filter(function(e){ return e.round === rq[0] && (!rq[1] || String(e.day) === rq[1]) && (ui.showSettled || e.status === 'pending' || ui.resDraft[e.k]); });
    list.sort(function(a, b){ return a.p.localeCompare(b.p) || a.stat.localeCompare(b.stat); });
    var rows = list.map(function(e){
      var v = resValue(e), s = draftStatus(v, e.line);
      return '<tr data-row="' + esc(e.k) + '">' +
        '<td class="who"><b>' + esc(e.p) + '</b> <small>' + esc(e.team || '') + '</small></td>' +
        '<td>' + STAT[e.stat] + ' ispod ' + fmt(e.line, 1) + '</td>' +
        '<td class="r">' + e.count + '</td>' +
        '<td><input type="text" inputmode="decimal" aria-label="Ostvareno" data-rf="actual" data-k="' + esc(e.k) + '" value="' + esc(v.actual) + '"></td>' +
        '<td><label class="cb"><input type="checkbox" data-rf="dnp" data-k="' + esc(e.k) + '"' + (v.dnp ? ' checked' : '') + '>Nije igrao</label></td>' +
        '<td class="r" style="color:var(--muted)" data-v="' + (e.r && e.r.min ? (parseInt(String(e.r.min), 10) || 0) : '') + '">' + (e.r && e.r.min ? esc(String(e.r.min).replace(/:\d+$/, '')) + ' min' : '') + '</td>' +
        '<td data-v="' + ({hit: 1, miss: 3, void: 2, pending: 4})[s] + '"><span class="tag ' + s + '" data-badge>' + STATUS_TXT[s] + '</span></td>' +
      '</tr>';
    }).join('');
    return '<section class="panel">' +
      '<p class="hint">Svaki par upisuješ samo jednom, a rezultat se primenjuje na sve tikete na kojima se pojavljuje. Upiši koliko je igrač ostvario na utakmici (poena, asistencija ili skokova), ili označi da nije igrao. Rezultate možeš i da tražiš od Claude-a u razgovoru, on ih preuzima sa zvaničnog sajta Evrolige.</p>' +
      '<div class="filters"><label class="f" style="flex-direction:row;align-items:center;gap:8px">Kolo <select data-act="resRound" style="width:auto">' +
        ropts.map(function(r){ var q = r.split(':'); return '<option value="' + esc(r) + '"' + (r === ui.resRound ? ' selected' : '') + '>' + esc(q[1] ? q[0] + ', dan ' + q[1] + ' (' + fmtDate((RD[q[0]] || [])[+q[1] - 1]) + ')' : q[0] + ((RD[q[0]] || []).length > 1 ? ', oba dana' : '')) + '</option>'; }).join('') + '</select></label>' +
        '<label class="cb" style="margin-left:8px"><input type="checkbox" data-act="toggleSettled"' + (ui.showSettled ? ' checked' : '') + '>Prikaži i već unete</label></div>' +
      (rows ? '<div class="scroll"><table class="res sortable" data-sid="res"><thead><tr><th data-col="0">Igrač</th><th data-col="1">Par</th><th data-col="2" class="r">Tiketa</th><th data-col="3">Ostvareno</th><th data-col="4">Nije igrao</th><th data-col="5" class="r">Minuta</th><th data-col="6">Status</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
        '<div class="btns"><button class="btn primary" data-act="saveResults"' + (busy ? ' disabled' : '') + '>' + (busy ? 'Čuvam…' : 'Sačuvaj rezultate') + '</button></div>'
        : '<p class="empty">Svi parovi iz ovog kola su već uneti.</p>') +
    '</section>';
  }

  function viewTickets(){
    if (!state.tickets.length) return '<section class="panel empty">Još nema tiketa.<br><button class="btn" data-act="tab" data-v="novi">Unesi prvi tiket</button></section>';
    var F = [['all','Svi'],['pending','U igri'],['won','Dobitni'],['lost','Gubitni']];
    var RDt = roundDays();
    var list = state.tickets.map(function(t, idx){ return {t:t, i:ticketInfo(t), idx: idx, miss: t.legs.filter(function(l){ return legStatus(t, l) === 'miss'; }).length}; }).filter(function(x){ return inScope(x.t, RDt) && (ui.tFilter === 'all' || x.i.st === ui.tFilter); });
    var TS = {nove: function(a, b){ return b.idx - a.idx; }, stare: function(a, b){ return a.idx - b.idx; }, kvotaV: function(a, b){ return b.i.odds - a.i.odds; }, kvotaM: function(a, b){ return a.i.odds - b.i.odds; }, parovi: function(a, b){ return b.t.legs.length - a.t.legs.length || b.idx - a.idx; }, pali: function(a, b){ return a.miss - b.miss || b.idx - a.idx; }, ulog: function(a, b){ return b.t.stake - a.t.stake || b.idx - a.idx; }, bilans: function(a, b){ return (b.i.payout - b.t.stake) - (a.i.payout - a.t.stake) || b.idx - a.idx; }};
    list.sort(TS[ui.tSort] || TS.nove);
    var shown = list.slice(0, ui.tLimit);
    var ST = {won:'Dobitan', lost:'Gubitan', pending:'U igri'};
    var html = shown.map(function(x){
      var t = x.t, i = x.i, open = !!ui.open[t.id];
      var body = '';
      if (open) {
        body = '<div class="tk-b"><div class="scroll"><table class="sortable" data-sid="tkl"><thead><tr><th data-col="0">Igrač</th><th data-col="1">Par</th><th data-col="2" class="r">Kvota</th><th data-col="3" class="r">Ostvareno</th><th data-col="4">Status</th></tr></thead><tbody>' + t.legs.map(function(l){
          var s = legStatus(t, l), r = state.results[keyOf(t, l)];
          var act = r && r.dnp ? 'nije igrao' : (r && r.actual != null ? fmt(r.actual, r.actual % 1 ? 1 : 0) + (r.min ? ' <small style="color:var(--muted)">(' + esc(String(r.min).replace(/:\d+$/, '')) + ' min)</small>' : '') : '');
          return '<tr><td>' + esc(l.p) + ' <small style="color:var(--muted)">' + esc(l.team || '') + '</small></td><td>' + STAT[l.stat] + ' ispod ' + fmt(l.line, 1) + '</td><td class="r">' + fmt(l.odds) + '</td><td class="r">' + act + '</td><td><span class="tag ' + s + '">' + STATUS_TXT[s] + '</span></td></tr>';
        }).join('') + '</tbody></table></div><div class="btns"><button class="btn sm" data-act="reuse" data-id="' + t.id + '">Iskoristi kao novi tiket</button><span style="display:inline-flex;gap:6px;align-items:center"><input type="text" inputmode="decimal" id="ref-' + t.id + '" placeholder="povraćaj" value="' + esc(t.refund || '') + '" style="width:100px;padding:4px 8px"><button class="btn sm" data-act="saveRefund" data-id="' + t.id + '">Sačuvaj povraćaj</button></span><button class="btn sm" data-act="fundToggle" data-id="' + t.id + '">' + (t.fund === 'dobitak' ? 'Označi kao svež novac' : 'Označi kao igrano iz dobitka') + '</button><button class="btn sm" data-act="delTicket" data-id="' + t.id + '">Obriši tiket</button></div></div>';
      }
      var miss = t.legs.filter(function(l){ return legStatus(t, l) === 'miss'; }).length;
      return '<article class="tk ' + i.st + '"><button class="tk-h" data-act="toggleTicket" data-id="' + t.id + '" aria-expanded="' + open + '">' +
        '<div><div class="main">' + parova(t.legs.length) + ', kvota ' + fmt(i.odds) + '</div><div class="meta">Kolo ' + esc(t.round) + ((RDt[String(t.round)] || []).length > 1 ? ', dan ' + dayOf(t, RDt) : '') + ', ' + esc(fmtDate(t.date)) + ', ulog ' + fmt(t.stake) + (t.fund === 'dobitak' ? ' iz dobitka' : '') + (miss ? ', palo ' + miss : '') + '</div></div>' +
        '<div class="right"><span class="tag ' + i.st + '">' + ST[i.st] + '</span><div class="meta">' + (i.st === 'won' ? '+' + fmt(i.payout - t.stake) : i.st === 'lost' ? (t.refund ? 'povraćaj ' + fmt(t.refund) + ', ' : '') + '−' + fmt(t.stake - (t.refund || 0)) : 'moguće ' + fmt(i.odds * t.stake)) + '</div></div>' +
      '</button>' + body + '</article>';
    }).join('');
    var SO = [['nove','Najnovije'],['stare','Najstarije'],['kvotaV','Najveća kvota'],['kvotaM','Najmanja kvota'],['parovi','Najviše parova'],['pali','Najmanje palih parova'],['ulog','Najveći ulog'],['bilans','Najbolji bilans']];
    return '<div class="filters">' + F.map(function(f){ return '<button class="btn sm' + (ui.tFilter === f[0] ? ' on' : '') + '" data-act="tFilter" data-v="' + f[0] + '">' + f[1] + '</button>'; }).join('') +
      '<button class="btn sm" data-act="fundAll" data-v="dobitak" title="Važi za sve tikete koji su trenutno prikazani">Sve prikazane: iz dobitka</button><button class="btn sm" data-act="fundAll" data-v="novi" title="Važi za sve tikete koji su trenutno prikazani">Sve prikazane: svež novac</button>' +
      '<label class="f" style="flex-direction:row;align-items:center;gap:6px;margin-left:auto">Poređaj <select data-act="tSort" style="width:auto">' + SO.map(function(o){ return '<option value="' + o[0] + '"' + ((ui.tSort || 'nove') === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select></label></div>' +
      (html || '<p class="empty">Nema tiketa u ovoj grupi.</p>') +
      (list.length > shown.length ? '<div class="btns"><button class="btn" data-act="more">Prikaži još (' + (list.length - shown.length) + ')</button></div>' : '');
  }

  function table(title, col, rows, note){
    if (!rows.length) return '';
    return '<section class="panel"><h2>' + title + '</h2>' + (note ? '<p class="hint">' + note + '</p>' : '') +
      '<div class="scroll"><table class="sortable" data-sid="' + sidOf(title) + '"><thead><tr><th data-col="0">' + col + '</th><th data-col="1" class="r">Parova</th><th data-col="2" class="r">Prošlo</th><th data-col="3" class="r">Procenat</th><th data-col="4">Ocena</th></tr></thead><tbody>' +
      rows.map(function(x){ var v = verdict(x); return '<tr><td>' + esc(x.k) + '</td><td class="r">' + x.n + '</td><td class="r">' + x.h + '</td><td class="r" data-v="' + x.rate + '">' + pct(x.rate) + '</td><td data-v="' + (x.n < 5 ? '' : (x.rate - x.be)) + '"><span class="tag ' + v[0] + '">' + v[1] + '</span></td></tr>'; }).join('') +
      '</tbody></table></div></section>';
  }
  function advice(sp, s, players, stats, spreads){
    var out = [];
    if (sp.length < 30) {
      out.push('Za sada je završeno ' + parova(sp.length) + '. Pouzdaniji zaključci kreću od 150 do 200 parova, do tada ocene uzmi kao naznaku, ne kao pravilo.');
    }
    if (sp.length) {
      var gap = s.prate - s.be;
      out.push('Minusi ti prolaze u ' + pct(s.prate) + ' slučajeva. ' +
        (gap >= 0 ? 'To je više nego što kvote predviđaju, što je dobar znak ako se zadrži na većem uzorku.' : 'To je manje nego što kvote predviđaju, znači da izbor parova za sada nema prednost nad kladionicom.'));
      var stl = scopedTickets(), legsAvg = stl.length ? stl.reduce(function(a, t){ return a + t.legs.length; }, 0) / stl.length : 0;
      if (legsAvg >= 2) {
        var n = Math.round(legsAvg);
        out.push('Sa tim procentom tiket od ' + n + ' parova prolazi otprilike ' + pct(Math.pow(s.prate, n)) + ' puta, a od 3 para ' + pct(Math.pow(s.prate, 3)) + '. Svaki par koji prolazi ređe nego što kvota predviđa dodatno smanjuje očekivani povraćaj celog tiketa.');
      }
    }
    var bad = players.filter(function(x){ return verdict(x)[0] === 'lose'; }).sort(function(a, b){ return (a.rate - a.be) - (b.rate - b.be); }).slice(0, 5);
    if (bad.length) out.push('Igraj manje: ' + bad.map(function(x){ return esc(x.k) + ' (' + x.h + ' od ' + x.n + ')'; }).join(', ') + '.');
    var good = players.filter(function(x){ return verdict(x)[0] === 'dobro'; }).sort(function(a, b){ return (b.rate - b.be) - (a.rate - a.be); }).slice(0, 5);
    if (good.length) out.push('Najbolje prolaze: ' + good.map(function(x){ return esc(x.k) + ' (' + x.h + ' od ' + x.n + ')'; }).join(', ') + '.');
    var st = stats.filter(function(x){ return x.n >= 15; }).sort(function(a, b){ return (b.rate - b.be) - (a.rate - a.be); });
    if (st.length >= 2) out.push('U odnosu na kvote, najbolje stoje ' + esc(st[0].k).toLowerCase() + ' (' + pct(st[0].rate) + '), a najslabije ' + esc(st[st.length - 1].k).toLowerCase() + ' (' + pct(st[st.length - 1].rate) + ').');
    return out.length ? '<section class="advice">' + out.map(function(p){ return '<p>' + p + '</p>'; }).join('') + '</section>' : '';
  }
  function cls(x){ return x > 0 ? 'pos' : x < 0 ? 'neg' : ''; }
  function rateCell(x){ return x && x.n ? pct(x.rate) + ' <small style="color:var(--muted)">(' + x.h + '/' + x.n + ')</small>' : '<span style="color:var(--muted)">–</span>'; }
  function simpleTable(title, note, head, rows){
    if (!rows.length) return '';
    return '<section class="panel"><h2>' + title + '</h2>' + (note ? '<p class="hint">' + note + '</p>' : '') +
      '<div class="scroll"><table class="sortable" data-sid="' + sidOf(title) + '"><thead><tr>' + head.map(function(h, k){ return '<th data-col="' + k + '"' + (k ? ' class="r"' : '') + '>' + h + '</th>'; }).join('') + '</tr></thead><tbody>' +
      rows.map(function(r){ return '<tr>' + r.map(function(c, k){ return '<td' + (k ? ' class="r"' : '') + '>' + c + '</td>'; }).join('') + '</tr>'; }).join('') +
      '</tbody></table></div></section>';
  }
  function byKey(list){ var m = {}; list.forEach(function(x){ m[String(x.k).toLowerCase()] = x; }); return m; }
  function lineBucket(e){
    var l = e.line;
    if (e.stat === 'P') return l < 8 ? 'Poeni do 7,5' : l < 13 ? 'Poeni 8 do 12,5' : 'Poeni 13 i više';
    if (e.stat === 'S') return l < 4 ? 'Skokovi do 3,5' : l < 6 ? 'Skokovi 4 do 5,5' : 'Skokovi 6 i više';
    return l < 3 ? 'Asistencije do 2,5' : l < 5 ? 'Asistencije 3 do 4,5' : 'Asistencije 5 i više';
  }
  function oddsBucket(e){ var o = e.avgOdds; return o < 1.75 ? 'Kvota do 1,74' : o < 1.85 ? 'Kvota 1,75 do 1,84' : o < 1.95 ? 'Kvota 1,85 do 1,94' : 'Kvota 1,95 i više'; }

  function stackTable(list){
    var st = list.filter(function(t){ return t.tag === 'stack'; });
    if (!st.length) return '';
    var rest = list.filter(function(t){ return t.tag !== 'stack'; });
    var row = function(lbl, L){ var w = 0, sk = 0, ret = 0, legs = 0, hit = 0, tot = 0; L.forEach(function(t){ var i = ticketInfo(t); if (i.st === 'won') w++; sk += t.stake; ret += i.payout; t.legs.forEach(function(l){ var s2 = legStatus(t, l); if (s2 === 'hit') hit++; if (s2 === 'hit' || s2 === 'miss') tot++; }); legs += t.legs.length; }); return [lbl, '' + L.length, '' + w, tot ? pct(hit / tot) : '–', '<span class="' + cls(ret - sk) + '">' + signed(ret - sk) + '</span>']; };
    return simpleTable('Tiketi oko jedne utakmice', 'Poređenje tiketa sa više parova iz iste utakmice i ostalih tiketa.', ['Vrsta','Tiketa','Dobitnih','Parovi prošli','Bilans'], [row('Oko jedne utakmice', st), row('Ostali', rest)]);
  }
  function ratingTable(sp){
    var withSc = sp.filter(function(e){ return e.sc != null; });
    var ord = ['Vrlo dobar', 'Dobar', 'Prosečan', 'Slab', 'Loš'];
    if (!withSc.length) return '<section class="panel"><h2>Da li ocena „Vrednost“ radi</h2><p class="hint">Od sada se uz svaki tiket iz Generatora pamti i ocena para. Kad se odigra par kola, ovde će se videti koliko stvarno prolaze parovi sa ocenom „Vrlo dobar“, a koliko oni sa ocenom „Loš“.</p></section>';
    var g = group(withSc, function(e){ return level(e.sc)[1]; }).sort(function(a, b){ return ord.indexOf(a.k) - ord.indexOf(b.k); });
    return table('Da li ocena „Vrednost“ radi', 'Ocena', g, 'Parovi po oceni koju su imali kad su odigrani. Ako ocena radi, procenat treba da raste od „Loš“ ka „Vrlo dobar“.');
  }
  function balanceChart(){
    var RD = roundDays(), pts = [], cumOwn = 0, cumNet = 0;
    rounds().forEach(function(r){ (RD[r] || []).forEach(function(d, i){
      var st = 0, ret = 0, own = 0, pend = false;
      state.tickets.forEach(function(t){ if (String(t.round) !== r || (t.date || '') !== d) return; var inf = ticketInfo(t); if (inf.st === 'pending') { pend = true; return; } st += t.stake; ret += inf.payout; if (t.fund !== 'dobitak') own += t.stake; });
      if (!st) return;
      cumOwn += own; cumNet += ret - st;
      pts.push({lbl: r + (RD[r].length > 1 ? '/' + (i + 1) : ''), own: cumOwn, net: cumNet});
    }); });
    if (pts.length < 2) return '';
    var W = 640, H = 220, P = 40, vals = [0]; pts.forEach(function(p){ vals.push(p.own, p.net); });
    var mn = Math.min.apply(null, vals), mx = Math.max.apply(null, vals); if (mx === mn) mx = mn + 1;
    var x = function(i){ return P + i * (W - 2 * P) / (pts.length - 1); }, y = function(v){ return H - P + 10 - (v - mn) / (mx - mn) * (H - 2 * P); };
    var line = function(key){ return pts.map(function(p, i){ return (i ? 'L' : 'M') + x(i).toFixed(1) + ' ' + y(p[key]).toFixed(1); }).join(' '); };
    var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" style="width:100%;max-width:' + W + 'px;height:auto" role="img" aria-label="Bilans kroz kola">' +
      '<line x1="' + P + '" x2="' + (W - P) + '" y1="' + y(0).toFixed(1) + '" y2="' + y(0).toFixed(1) + '" stroke="currentColor" stroke-opacity=".25"/>' +
      '<path d="' + line('own') + '" fill="none" stroke="var(--muted)" stroke-width="2" stroke-dasharray="5 4"/>' +
      '<path d="' + line('net') + '" fill="none" stroke="var(--accent)" stroke-width="3"/>' +
      pts.map(function(p, i){ return '<circle cx="' + x(i).toFixed(1) + '" cy="' + y(p.net).toFixed(1) + '" r="4" fill="var(--accent)"/><text x="' + x(i).toFixed(1) + '" y="' + (H - 8) + '" text-anchor="middle" font-size="12" fill="currentColor" opacity=".7">' + esc(p.lbl) + '</text><text x="' + x(i).toFixed(1) + '" y="' + (y(p.net) - 9).toFixed(1) + '" text-anchor="middle" font-size="12" fill="currentColor">' + esc(fmt(p.net, 0)) + '</text>'; }).join('') + '</svg>';
    return '<section class="panel"><h2>Bilans kroz kola</h2><p class="hint">Narandžasta linija je ukupan bilans posle svakog dana kola (kolo/dan). Isprekidana linija je ukupno uložen svež novac.</p>' + svg + '</section>';
  }
  function exactLineTable(sp){
    var LS = state.lineStats && state.lineStats.t || {}, mine = {}, keys = {};
    sp.forEach(function(e){ if (e.stat !== 'A' && e.stat !== 'S') return; var k = e.stat + e.line; keys[k] = 1; (mine[k] = mine[k] || []).push(e); });
    Object.keys(LS).forEach(function(k){ if (k[0] === 'A' || k[0] === 'S') keys[k] = 1; });
    var ks = Object.keys(keys).sort(function(a, b){ return a[0] !== b[0] ? (a[0] === 'A' ? -1 : 1) : parseFloat(a.slice(1)) - parseFloat(b.slice(1)); });
    if (!ks.length) return '';
    var tag = function(x){ var v = verdict(x); return '<span class="tag ' + v[0] + '">' + v[1] + '</span>'; };
    var rows = ks.map(function(k){
      var L = mine[k] || [], m = null, o = null;
      if (L.length) { var h = 0, be = 0; L.forEach(function(e){ if (e.status === 'hit') h++; be += 1 / e.avgOdds; }); m = {n:L.length, h:h, rate:h / L.length, be:be / L.length}; }
      var t = LS[k]; if (t) o = {n:t[0], h:t[1], rate:t[1] / t[0], be:t[5] != null ? t[5] : 1 / t[3]};
      var lbl = (k[0] === 'A' ? 'Asistencije ' : 'Skokovi ') + String(k.slice(1)).replace('.', ',');
      return [esc(lbl), rateCell(m), m ? tag(m) : '–', rateCell(o), o ? tag(o) : '–'];
    });
    var at = state.lineStats && state.lineStats.src ? ' Cela ponuda: ' + esc(state.lineStats.src) : '';
    return simpleTable('Tačna granica: asistencije i skokovi', 'Koliko često je minus prošao na svakoj tačnoj liniji. Tvoji minusi su parovi sa tvojih tiketa (svaki par jednom po kolu). Cela ponuda su svi minusi koje je kladionica nudila na tu liniju, bez obzira da li si ih igrao, pa pokazuje kako linija prolazi sama po sebi.' + at,
      ['Granica','Tvoji minusi','Ocena','Cela ponuda','Ocena'], rows);
  }
  function minutesTable(sp){
    var withMin = sp.filter(function(e){ return e.r && e.r.min; });
    if (withMin.length < 5) return '';
    var g = group(withMin, function(e){ var m = parseInt(String(e.r.min), 10) || 0; return m < 15 ? 'Do 15 minuta' : m < 22 ? '15 do 22 minuta' : '22 minuta i više'; });
    var ord = ['Do 15 minuta','15 do 22 minuta','22 minuta i više'];
    g.sort(function(a, b){ return ord.indexOf(a.k) - ord.indexOf(b.k); });
    return table('Po odigranim minutima', 'Minutaža', g, 'Koliko minuta je igrač stvarno proveo na terenu. Minusi prirodno prolaze češće kad igrač igra malo, pa ova tabela pokazuje koliko ti rezultat zavisi od minutaže.');
  }
  function viewAnalysis(){
    var sp = settledPicks(), s = summary();
    var SECS = [['pregled','Pregled'],['igraci','Igrači'],['timovi','Timovi'],['linije','Linije i kvote'],['tiketi','Tiketi i kola'],['kopija','Rezervna kopija']];
    var sec = ui.aSec || 'pregled';
    var nav = '<div class="filters">' + SECS.map(function(x){ return '<button class="btn sm' + (sec === x[0] ? ' on' : '') + '" data-act="aSec" data-v="' + x[0] + '">' + x[1] + '</button>'; }).join('') + '</div>';
    var backup = '<section class="panel"><h2>Rezervna kopija</h2><p class="hint">Izvezi podatke povremeno i sačuvaj ih negde. Uvoz zamenjuje sve postojeće podatke.</p>' +
      '<div class="btns" style="margin-top:0"><button class="btn" data-act="export">Prikaži podatke za kopiranje</button><button class="btn" data-act="import">Uvezi iz polja ispod</button></div>' +
      '<textarea id="ioBox" style="margin-top:10px" placeholder="Ovde se pojavljuju izvezeni podaci, ili nalepi podatke za uvoz"></textarea></section>';
    if (sec === 'kopija') return nav + backup;
    if (!sp.length) return nav + '<section class="panel empty">Analiza se pojavljuje kada uneseš rezultate za bar nekoliko parova.<br><button class="btn" data-act="tab" data-v="rezultati">Unesi rezultate</button></section>';

    var players = group(sp, function(e){ return e.p; }).sort(function(a, b){ return b.n - a.n || a.rate - b.rate; });
    var stats = group(sp, function(e){ return STAT[e.stat]; });
    var spreads = group(sp, spreadBucket);

    if (sec === 'pregled') {
      var expHits = sp.reduce(function(a, e){ return a + 1 / e.avgOdds; }, 0);
      var geo = Math.exp(sp.reduce(function(a, e){ return a + Math.log(e.avgOdds); }, 0) / sp.length);
      var calib = '<section class="panel"><h2>Tvoj procenat naspram kladionice</h2><p class="hint">Po kvotama je trebalo da prođe oko ' + fmt(expHits, 1) + ' od ' + sp.length + ' parova (kvote sadrže i maržu kladionice). Prošlo je ' + s.ph + ', što je ' + (s.ph >= expHits ? fmt(s.ph - expHits, 1) + ' više' : fmt(expHits - s.ph, 1) + ' manje') + ' od toga. Prosečna kvota po paru je ' + fmt(geo) + '.</p></section>';
      var ev = [];
      [1,2,3,4,5,6,8,10].forEach(function(n){
        var pass = Math.pow(s.prate, n), odds = Math.pow(geo, n), roi = pass * odds - 1;
        ev.push(['' + n, pct(pass), fmt(odds), '<span class="' + cls(roi) + '">' + (roi > 0 ? '+' : '') + pct(roi) + '</span>']);
      });
      var evTable = simpleTable('Očekivani povraćaj po broju parova', 'Računato sa tvojim trenutnim procentom po paru (' + pct(s.prate) + ') i prosečnom kvotom ' + fmt(geo) + '. Pretpostavlja da je procent stvaran i da se zadrži, što na malom uzorku nije sigurno. Pokazuje kako broj parova pojačava i prednost i gubitak.', ['Parova','Tiket prolazi','Kvota','Očekivani povraćaj'], ev);
      var statRows = stats.map(function(x){ var v = verdict(x); return [esc(x.k), '' + x.n, pct(x.rate), '<span class="tag ' + v[0] + '">' + v[1] + '</span>']; });
      var nR = rounds().length, RV = state.review, due = RV && RV.n ? nR >= RV.n + 3 : nR >= 3;
      var reminder = RV && RV.n && !due ? '<section class="advice" style="border-left-color:var(--line)"><p><b>Poslednja provera: ' + esc(RV.at) + ', posle ' + RV.n + '. kola.</b> ' + esc(RV.sum || '') + ' Sledeća provera posle ' + (RV.n + 3) + '. kola.</p></section>' : '<section class="advice" style="border-left-color:' + (due ? 'var(--accent)' : 'var(--line)') + '"><p><b>' + (due ? 'Vreme je za proveru.' : 'Sledeća provera: posle 3. kola.') + '</b> ' + (due ? 'Imaš podatke iz ' + nR + ' kola. Pitaj Claude-a u razgovoru za analizu: da li ocene „Šansa“ i „Vrednost“ stvarno razlikuju dobre i loše parove, da li tiketi oko jedne utakmice prolaze češće, kako prolaze igrači sa malo minuta i da li treba menjati broj parova ili ulog.' : 'Za sada je odigrano ' + nR + ' kolo. Posle 3. kola pitaj Claude-a za analizu da li nešto u načinu igranja ili u aplikaciji treba menjati.') + '</p></section>';
      return nav + reminder + advice(sp, s, players, stats, spreads) + balanceChart() + ratingTable(sp) +
        simpleTable('Po statistici', '', ['Statistika','Parova','Prošlo','Ocena'], statRows) + evTable;
    }

    if (sec === 'igraci') {
      var ps = group(sp, function(e){ return e.p + ', ' + STAT[e.stat].toLowerCase(); }).sort(function(a, b){ return b.n - a.n || a.rate - b.rate; });
      var byP = {};
      sp.forEach(function(e){ var k = e.p.toLowerCase(); byP[k] = byP[k] || {tk:0, lines:{}}; byP[k].tk += e.count; });
      var pRows = players.map(function(x){
        var v = verdict(x), sub = {};
        ['P','S','A'].forEach(function(st){ sub[st] = group(sp.filter(function(e){ return e.p.toLowerCase() === String(x.k).toLowerCase() && e.stat === st; }), function(){ return 'x'; })[0]; });
        return [esc(x.k), rateCell(x), rateCell(sub.P), rateCell(sub.S), rateCell(sub.A), '' + (byP[String(x.k).toLowerCase()] || {}).tk, '<span class="tag ' + v[0] + '">' + v[1] + '</span>'];
      });
      return nav + simpleTable('Po igraču', 'Svaki izbor se računa jednom, bez obzira na koliko tiketa je bio. Kolona Tiketa pokazuje na koliko tiketa je igrač bio ukupno. Ocena traži bar 5 izbora i razliku od 5 procentnih poena u odnosu na ono što kvote predviđaju.',
        ['Igrač','Ukupno','Poeni','Skokovi','Asistencije','Tiketa','Ocena'], pRows) +
        table('Igrač i statistika', 'Izbor', ps.slice(0, 60), ps.length > 60 ? 'Prikazano 60 najčešćih.' : '');
    }

    if (sec === 'timovi') {
      var TK = {}; sp.forEach(function(e){ if (e.team) { var k0 = nkey(e.team), o = TK[k0] = TK[k0] || {names: {}}; o.names[e.team] = (o.names[e.team] || 0) + 1; } }); var rootOf = function(k){ var r = k; Object.keys(TK).forEach(function(k2){ if (k2.length > r.length && k2.indexOf(r + ' ') === 0) r = k2; }); return r; }; var NM = {}; Object.keys(TK).forEach(function(k){ var r = rootOf(k), m = NM[r] = NM[r] || {}; Object.keys(TK[k].names).forEach(function(n){ m[n] = (m[n] || 0) + TK[k].names[n]; }); }); var canonT = function(n){ var m = NM[rootOf(nkey(n))]; if (!m) return n; return Object.keys(m).sort(function(a, b){ return m[b] - m[a] || b.length - a.length; })[0]; };
      var teams = group(sp, function(e){ return e.team ? canonT(e.team) : null; }).sort(function(a, b){ return b.n - a.n; });
      var tRows = teams.map(function(x){
        var v = verdict(x), sub = {};
        ['P','S','A'].forEach(function(st){ sub[st] = group(sp.filter(function(e){ return e.team && canonT(e.team) === String(x.k) && e.stat === st; }), function(){ return 'x'; })[0]; });
        return [esc(x.k), rateCell(x), rateCell(sub.P), rateCell(sub.S), rateCell(sub.A), '<span class="tag ' + v[0] + '">' + v[1] + '</span>'];
      });
      var noTeam = sp.filter(function(e){ return !e.team; }).length;
      return nav + simpleTable('Po timu', 'Procenat minusa koji su prošli za igrače svakog tima, ukupno i po statistici. U zagradi je prošlo od ukupno.' + (noTeam ? ' ' + noTeam + ' izbora nema upisan tim i nisu uračunati.' : ''),
        ['Tim','Ukupno','Poeni','Skokovi','Asistencije','Ocena'], tRows);
    }

    if (sec === 'linije') {
      var order = ['Poeni do 7,5','Poeni 8 do 12,5','Poeni 13 i više','Skokovi do 3,5','Skokovi 4 do 5,5','Skokovi 6 i više','Asistencije do 2,5','Asistencije 3 do 4,5','Asistencije 5 i više'];
      var lines = group(sp, lineBucket).sort(function(a, b){ return order.indexOf(a.k) - order.indexOf(b.k); });
      var oOrder = ['Kvota do 1,74','Kvota 1,75 do 1,84','Kvota 1,85 do 1,94','Kvota 1,95 i više'];
      var odds = group(sp, oddsBucket).sort(function(a, b){ return oOrder.indexOf(a.k) - oOrder.indexOf(b.k); });
      return nav + table('Visina linije', 'Linija', lines) +
        exactLineTable(sp) + table('Visina kvote', 'Kvota', odds, 'Niža kvota znači da kladionica minus smatra verovatnijim.') + minutesTable(sp);
    }

    // tiketi i kola
    var settledT = scopedTickets().filter(function(t){ return ticketInfo(t).st !== 'pending'; });
    var byLen = {}, lens = [];
    settledT.forEach(function(t){
      var i = ticketInfo(t), n = t.legs.length;
      if (!byLen[n]) { byLen[n] = {c:0, w:0, st:0, ret:0}; lens.push(n); }
      byLen[n].c++; byLen[n].st += t.stake; byLen[n].ret += i.payout; if (i.st === 'won') byLen[n].w++;
    });
    lens.sort(function(a, b){ return a - b; });
    var lenRows = lens.map(function(n){ var x = byLen[n], p = x.ret - x.st; return ['' + n, '' + x.c, '' + x.w, pct(x.w / x.c), pct(Math.pow(s.prate, n)), '<span class="' + cls(p) + '">' + signed(p) + '</span>']; });

    var dist = {}, oneMiss = 0, refSum = 0, refN = 0;
    settledT.forEach(function(t){ var m = t.legs.filter(function(l){ return legStatus(t, l) === 'miss'; }).length; var k = m >= 4 ? '4 i više' : '' + m; dist[k] = (dist[k] || 0) + 1; if (m === 1) oneMiss++; if (t.refund) { refSum += t.refund; refN++; } });
    var distRows = ['0','1','2','3','4 i više'].filter(function(k){ return dist[k]; }).map(function(k){ return [k === '0' ? '0 (dobitan)' : k, '' + dist[k], pct(dist[k] / settledT.length)]; });

    var killers = sp.filter(function(e){ return e.status === 'miss'; }).map(function(e){
      var stake = 0; scopedTickets().forEach(function(t){ if (t.legs.some(function(l){ return keyOf(t, l) === e.k; })) stake += t.stake; });
      return {e: e, stake: stake};
    }).sort(function(a, b){ return b.e.count - a.e.count || b.stake - a.stake; }).slice(0, 12);
    var killRows = killers.map(function(x){ var e = x.e; return [esc(e.p) + ' <small style="color:var(--muted)">' + esc(e.team || '') + '</small>', STAT[e.stat] + ' ispod ' + fmt(e.line, 1), '' + e.count, fmt(x.stake)]; });

    var RDa = roundDays(), rs = [];
    rounds().forEach(function(r){
      var days = RDa[r] || [''], parts = days.length > 1 ? days.map(function(d, i){ return {lbl: 'dan ' + (i + 1) + ' (' + fmtDate(d) + ')', f: function(t){ return dayOf(t, RDa) === i + 1; }, day: i + 1}; }).concat([{lbl: 'oba dana', f: function(){ return true; }, day: 0}]) : [{lbl: days[0] ? fmtDate(days[0]) : '', f: function(){ return true; }, day: 0}];
      parts.forEach(function(pt){
        var o = {t:0, st:0, ret:0, w:0, re:0};
        state.tickets.forEach(function(t){ if (String(t.round) !== r || !inScope(t, RDa) || !pt.f(t)) return; var i = ticketInfo(t); if (i.st === 'pending') return; o.t++; o.st += t.stake; o.ret += i.payout; if (i.st === 'won') o.w++; o.re += t.stake - (t.freshAmt != null ? t.freshAmt : (t.fund === 'dobitak' ? 0 : t.stake)); });
        if (!o.t) return;
        var g = group(sp.filter(function(e){ return e.round === r && (!pt.day || e.day === pt.day); }), function(){ return 'x'; })[0];
        rs.push([(pt.day === 0 && days.length > 1 ? '<b>' : '') + esc(r) + (pt.lbl ? ', ' + esc(pt.lbl) : '') + (pt.day === 0 && days.length > 1 ? '</b>' : ''), '' + o.t, '' + o.w, fmt(o.st), fmt(o.re), fmt(o.ret), '<span class="' + cls(o.ret - o.st) + '">' + signed(o.ret - o.st) + '</span>', g ? pct(g.rate) : '–']);
      });
    });

    return nav +
      simpleTable('Po kolu i danu', 'Kolona „Iz dobitka“ pokazuje koliko je od uloga odigrano novcem dobijenim ranije, a ne svežim novcem.', ['Kolo','Tiketa','Dobitnih','Uloženo','Iz dobitka','Vraćeno','Bilans','Parovi prošli'], rs) +
      simpleTable('Broj parova na tiketu', 'Očekivano je koliko često bi tiket prolazio da svaki par prolazi tvojim ukupnim procentom.', ['Parova','Tiketa','Dobitnih','Procenat','Očekivano','Bilans'], lenRows) +
      stackTable(settledT) +
      simpleTable('Koliko parova padne po tiketu', (oneMiss ? oneMiss + ' tiketa je palo zbog samo jednog para.' : '') + (refN ? ' Za ' + refN + ' od njih stigao je povraćaj, ukupno ' + fmt(refSum) + ' din, i uračunat je u bilans.' : ''), ['Palo parova','Tiketa','Udeo'], distRows) +
      simpleTable('Izbori koji su oborili najviše tiketa', 'Pali minusi poređani po broju tiketa na kojima su bili. Isti izbor na mnogo tiketa znači da jedan pogrešan izbor obara veliki deo uloga.', ['Igrač','Par','Tiketa','Ulog na tim tiketima'], killRows);
  }


  /* ---------- generator ---------- */
  var BOOKMARKLET_MB = "javascript:!function(){if(window.__mbPanel)window.__mbPanel.style.display=\"block\";else{var e=\"mt-maxbet-plan\",t={P:\"poeni\",A:\"asist.\",S:\"skokovi\"},a={P:[\"ouPlPoints\",\"51681\",\"51679\"],A:[\"ouPlAssists\",\"51684\",\"51682\"],S:[\"ouPlRebounds\",\"51687\",\"51685\"]},n=\"https://feeds.incrowdsports.com/provider/euroleague-feeds/v3/competitions/E/statistics/\",i=\"https://api-live.euroleague.net/v2/competitions/E/seasons/\",r=[\"nedelja\",\"ponedeljak\",\"utorak\",\"sreda\",\"četvrtak\",\"petak\",\"subota\"],o=function(){try{return JSON.parse(localStorage.getItem(e)||\"null\")}catch(e){return null}}(),l=[],s=document.createElement(\"div\");window.__mbPanel=s,s.style.cssText=\"position:fixed;left:12px;bottom:12px;width:340px;max-height:80vh;overflow:auto;z-index:2147483647;background:#fff;color:#15223a;border:2px solid #1f6feb;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.35);font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;padding:12px\",document.body.appendChild(s),s.addEventListener(\"click\",async function(e){var t=e.target.closest(\"[data-a]\");if(t){var f=t.getAttribute(\"data-a\");if(\"build\"===f)return void async function(){if(y||!o||!o.tickets)return;var e=o.tickets[o.idx||0];if(!e)return;y=!0,l=[],e.marks={},h();try{if(!document.querySelector(\"ion-grid.es-match\"))throw new Error(\"Otvori ponudu Poeni igrača EUROLEAGUE (lista igrača), pa klikni ponovo.\");if(!await async function(){if(!E())return!0;var e=document.querySelector(\"ion-button.ticket--empty-btn\");if(!e)return!1;e.click(),await x(600);var t=document.querySelector(\"ion-alert\");if(t&&E()){var a=t.querySelectorAll(\"button\");a.length&&a[a.length-1].click(),await x(600)}return!!await S(function(){return!E()},3e3)}())throw new Error(\"Tiket nije prazan. Obriši ga ručno (kanta na tiketu) pa klikni ponovo.\");for(var t=e.legs.slice().sort(function(e,t){return(\"P\"===e.s?0:1)-(\"P\"===t.s?0:1)}),a=[],n=0,i=0;i<t.length;i++){var r,s=t[i];try{r=await N(s,a)}catch(e){r={ok:!1,msg:\"greška: \"+(e.message||e)}}e.marks[s.c+s.s]=r,r.ok&&n++,h(),await x(250)}await M(),await x(400),e.actual=a,e.built=n>0;var u=function(e){var t=document.querySelector(\"ion-input.ticket-payin-input-field input\")||document.querySelector(\".ticket-payin-input input\");if(!t)return!1;var a=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,\"value\");return t.focus(),a&&a.set?a.set.call(t,String(e)):t.value=String(e),[\"input\",\"change\",\"keyup\"].forEach(function(e){t.dispatchEvent(new Event(e,{bubbles:!0}))}),t.blur(),t.dispatchEvent(new Event(\"blur\",{bubbles:!0})),!0}(e.stake);l.unshift(\"Dodato \"+n+\" od \"+e.legs.length+\" parova. Na tiketu: \"+E()+\".\"),l.push(u?\"Ulog \"+e.stake+\" din je upisan. Proveri iznos na tiketu.\":\"Polje za ulog nije pronađeno, upiši ulog ručno.\"),n<e.legs.length&&l.push(\"Neki parovi nisu dodati (označeni crveno). Možeš ih dodati ručno ili igrati tiket bez njih.\"),l.push(\"Proveri tiket i klikni UPLATI, pa ovde Odigran ✓.\");var c=[].slice.call(document.querySelectorAll(\"ds-navbar-bottom-ticket button, ds-navbar-bottom-ticket ion-button\")).filter(function(e){return/UPLATI/i.test(e.textContent||\"\")})[0];if(c){c.style.outline=\"3px solid #1f6feb\",c.style.outlineOffset=\"2px\";try{c.scrollIntoView({block:\"center\",behavior:\"smooth\"})}catch(e){}}}catch(e){l.push(e.message||String(e))}y=!1,m(),h()}();if(\"unbuild\"===f){var k=o.tickets[o.idx||0];return k&&(k.built=!1,k.actual=null,k.marks={}),m(),l=[],void h()}if(\"close\"!==f)if(\"showplan\"!==f)if(\"loadplan\"!==f){if(\"next\"===f||\"prev\"===f)return o.idx=Math.max(0,Math.min((o.idx||0)+(\"next\"===f?1:-1),o.tickets.length)),m(),l=[],void h();if(\"played\"===f){var w=o.tickets[o.idx||0];return w&&(w.done=!0,o.idx=Math.min((o.idx||0)+1,o.tickets.length),m(),l=[\"Tiket označen kao odigran.\"]),void h()}if(\"copyplayed\"!==f){if(\"offer\"===f){var j;l=[\"Preuzimam ponudu sa MaxBeta…\"],h();try{j=await async function(){var e=location.origin+\"/restapi/offer/sr/\",t=null;try{((await g(e+\"categories/sport/SK/l?annex=3&locale=sr\",!0)).categories||[]).forEach(function(e){!t&&/poeni igra.a euroleague/i.test(e.name||\"\")&&(t=e.id)})}catch(e){}t||(t=\"194042\");var n=await g(e+\"sport/SK/league/\"+t+\"/mob?annex=3&locale=sr\",!0),i=[];return(n.esMatches||[]).forEach(function(e){if(!e.blocked&&!e.live){var t=e.odds||{},n=e.params||{};Object.keys(a).forEach(function(o){var l,s,u=a[o],c=p(n[u[0]]),f=p(t[u[1]]),g=p(t[u[2]]);null!=c&&f&&i.push({c:String(e.matchCode),p:e.home,t:e.away,s:o,l:c,u:f,o:g,time:(l=e.kickOffTime,s=new Date(l),r[s.getDay()]+\", \"+d(s.getDate())+\". \"+d(s.getMonth()+1)+\". \"+s.getFullYear()+\". \"+d(s.getHours())+\":\"+d(s.getMinutes())),id:e.id})})}}),i}()}catch(e){return l=[\"Ponuda nije preuzeta: \"+(e.message||e)+\". Otvori MaxBet stranicu i pokušaj ponovo.\"],void h()}if(!j.length)return l=[\"U ponudi Poeni igrača EUROLEAGUE trenutno nema igrača.\"],void h();l=[\"Ponuda: \"+j.length+\" linija. Preuzimam statistiku sa Evrolige…\"],h();var P={};j.forEach(function(e){P[e.t]=1});var O=null,q=\"\";try{O=await async function(e){var t=new Date,a=t.getMonth()>=6?t.getFullYear():t.getFullYear()-1,r=\"E\"+a,o=\"E\"+(a-1),l=function(e){return g(e+\"&phaseTypeCode=RS\").then(function(t){return t.players&&t.players.length||t.teams&&t.teams.length?t:g(e)},function(){return g(e)})},s=function(){return{teams:[]}},p=await Promise.all([l(n+\"players/traditional?seasonMode=Single&limit=3000&statisticMode=perGame&seasonCode=\"+r),g(i+r+\"/games\"),l(n+\"teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+r).catch(s),g(n+\"teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+o).catch(s),l(n+\"teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+r).catch(s),g(n+\"teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+o).catch(s)]),d={season:r,at:t.toISOString(),players:{},games:[],clubs:{},def:{cur:{},prev:{}},rosters:{},tmap:{}};(p[0].players||[]).forEach(function(e){var t=e.gamesPlayed||0;t&&(d.players[c(e.player.name)]=[t,Math.round(10*e.minutesPlayed)/10,e.pointsScored,e.totalRebounds,e.assists,String(e.player.team&&e.player.team.code||\"\").split(\";\").pop(),e.foulsCommited||0],d.perGame=!0)});var f=function(e){return e.twoPointersAttempted+e.threePointersAttempted+.44*e.freeThrowsAttempted-e.offensiveRebounds+e.turnovers};[[\"cur\",p[2],p[4]],[\"prev\",p[3],p[5]]].forEach(function(e){var t={};(e[2].teams||[]).forEach(function(e){t[e.team.code]=f(e)}),(e[1].teams||[]).forEach(function(a){var n=f(a),i=t[a.team.code]||n;d.def[e[0]][a.team.code]=[a.gamesPlayed,a.pointsScored,a.totalRebounds,a.assists,Math.round((n+i)/2*10)/10,Math.round(a.pointsScored/n*1e3)/10]})});var m=t.getTime()-432e5,v=t.getTime()+3456e5;return(p[1].data||[]).forEach(function(e){var t=Date.parse(e.utcDate||e.date);t>=m&&t<=v&&!e.played&&([e.local.club,e.road.club].forEach(function(e){d.clubs[e.code]={name:e.name,abbr:e.abbreviatedName||\"\",ed:e.editorialName||\"\"}}),d.games.push({d:e.utcDate||e.date,h:e.local.club.code,a:e.road.club.code}))}),e.forEach(function(e){var t=u(e).split(\" \"),a=null,n=0;Object.keys(d.clubs).forEach(function(e){var i=d.clubs[e],r=u(i.name+\" \"+i.abbr+\" \"+i.ed).split(\" \"),o=0;t.forEach(function(e){e.length>2&&r.indexOf(e)>=0&&(o+=e.length)}),o>n&&(n=o,a=e)}),a&&(d.tmap[e]=a)}),await Promise.all(Object.keys(d.clubs).map(function(e){return g(i+r+\"/clubs/\"+e+\"/people\").then(function(t){d.rosters[e]=(t||[]).filter(function(e){return\"J\"===e.type&&!1!==e.active&&e.person}).map(function(e){return[c(e.person.name),e.positionName||\"\",e.person.name]})}).catch(function(){})})),d}(Object.keys(P))}catch(e){q=e.message||\"greška\"}T=JSON.stringify({v:2,src:\"maxbet\",at:(new Date).toISOString(),picks:j,el:O});var A=O?\"Statistika: \"+Object.keys(O.players).length+\" igrača, \"+O.games.length+\" utakmica.\":\"Statistika nije preuzeta (\"+q+\"), kopirana je samo ponuda.\";v(T).then(function(e){l=[A,e?\"Ponuda kopirana (\"+j.length+\" linija). Nalepi je u aplikaciju, Generator.\":\"Kopiranje nije uspelo, kopiraj tekst ispod ručno.\"],h(),e||b(T)})}}else{var T,z=o.tickets.filter(function(e){return e.done}).map(function(e){return{stake:e.stake,legs:(e.built&&e.actual&&e.actual.length?e.actual:e.legs).map(function(e){return{c:e.c,p:e.p,t:e.t||\"\",s:e.s,l:e.l,u:e.u}})}});v(T=JSON.stringify({v:1,kind:\"played\",round:o.round||\"\",at:(new Date).toISOString(),tickets:z})).then(function(e){l=[e?\"Kopirano \"+z.length+\" odigranih tiketa.\":\"Kopiranje nije uspelo, kopiraj tekst ispod ručno.\"],h(),e||b(T)})}}else{try{var C=JSON.parse(s.querySelector(\"#mb-plan\").value.trim());if(!C||!Array.isArray(C.tickets)||!C.tickets.length)throw 0;C.idx=0,o=C,m(),l=[\"Plan učitan: \"+C.tickets.length+\" tiketa.\"]}catch(e){l=[\"Plan nije ispravan. Kopiraj ga ponovo iz aplikacije.\"]}h()}else{var D=s.querySelector(\"#mb-planbox\");D.style.display=\"none\"===D.style.display?\"block\":\"none\"}else s.style.display=\"none\"}}),h()}function u(e){var t=String(e||\"\").normalize(\"NFD\").replace(/[\\u0300-\\u036f]/g,\"\").toLowerCase().replace(/đ/g,\"dj\");return(t=t.replace(/\\b([a-z])\\.\\s*([a-z])\\./g,\"$1$2\").replace(/[-.]/g,\" \").replace(/[^a-z ]/g,\"\")).split(/\\s+/).filter(function(e){return e&&[\"jr\",\"sr\",\"ii\",\"iii\",\"iv\"].indexOf(e)<0}).join(\" \")}function c(e){if(e.indexOf(\",\")>=0){var t=e.split(\",\");return u(t[1]+\" \"+t[0])}return u(e)}function p(e){var t=parseFloat(String(null==e?\"\":e).replace(\",\",\".\"));return isFinite(t)?t:null}function d(e){return(e<10?\"0\":\"\")+e}function f(e){return String(null==e?\"\":e).replace(/[&<>\"]/g,function(e){return{\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\",'\"':\"&quot;\"}[e]})}async function g(e,t){var a=await fetch(e,{credentials:t?\"include\":\"omit\"});if(!a.ok)throw new Error(\"HTTP \"+a.status);return a.json()}function m(){try{localStorage.setItem(e,JSON.stringify(o))}catch(e){}}function v(e){function t(){var t=document.createElement(\"textarea\");t.value=e,t.style.cssText=\"position:fixed;left:-9999px\",document.body.appendChild(t),t.select();var a=!1;try{a=document.execCommand(\"copy\")}catch(e){}return t.remove(),a}return navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(e).then(function(){return!0},function(){return t()}):Promise.resolve(t())}function k(e,t,a){return'<button data-a=\"'+t+'\" style=\"margin:3px 4px 3px 0;padding:6px 10px;border-radius:4px;cursor:pointer;font:inherit;font-weight:600;border:1px solid '+(a?\"#1f6feb;background:#1f6feb;color:#fff\":\"#b8c0cc;background:#f4f6f9;color:#15223a\")+'\">'+e+\"<\/button>\"}function h(){var e='<div style=\"display:flex;justify-content:space-between;align-items:center\"><b style=\"font-size:15px\">MaxBet pomoćnik<\/b>'+k(\"×\",\"close\")+\"<\/div>\";if(e+=\"<div>\"+k(\"Kopiraj ponudu i statistiku\",\"offer\",!0)+k(\"Nalepi plan\",\"showplan\")+\"<\/div>\",e+='<div id=\"mb-planbox\" style=\"display:none\"><textarea id=\"mb-plan\" style=\"width:100%25;height:80px;font:11px monospace\" placeholder=\"Nalepi plan iz aplikacije\"><\/textarea>'+k(\"Učitaj plan\",\"loadplan\",!0)+\"<\/div>\",o&&o.tickets&&o.tickets.length){var a=o.idx||0,n=o.tickets[a];e+='<div style=\"margin-top:8px;padding-top:8px;border-top:1px solid #ddd\">Plan: <b>'+o.tickets.length+\" tiketa<\/b>\"+(o.round?\", kolo \"+f(o.round):\"\")+\"<\/div>\",n?(e+='<div style=\"margin:6px 0\"><b>Tiket '+(a+1)+\" od \"+o.tickets.length+\"<\/b>, ulog \"+f(n.stake)+\" din, \"+n.legs.length+\" parova<\/div>\",e+='<ol style=\"margin:0 0 6px;padding-left:20px\">'+n.legs.map(function(e){var a=(n.marks||{})[e.c+e.s];return\"<li>\"+(a?'<span style=\"color:'+(a.ok?\"#1d7a4b\":\"#b2261e\")+'\">'+(a.ok?\"✓ \":\"✗ \")+\"<\/span>\":\"\")+\"<b>\"+f(e.c)+\"<\/b> \"+f(e.p)+\", \"+t[e.s]+\" manje \"+e.l+\" @ \"+e.u+(a&&a.msg?' <i style=\"color:'+(a.ok?\"#8a6d00\":\"#b2261e\")+'\">'+f(a.msg)+\"<\/i>\":\"\")+\"<\/li>\"}).join(\"\")+\"<\/ol>\",e+='<div style=\"display:flex;gap:6px\">'+k(\"‹ Prethodni\",\"prev\")+k(\"Sledeći ›\",\"next\")+\"<\/div>\",e+=\"<div>\"+k(y?\"Slažem…\":\"Složi tiket \"+(a+1),\"build\",!0)+(n.built?k(\"Odigran ✓\",\"played\",!0)+k(\"Nisam uplatio\",\"unbuild\"):k(\"Odigran ✓\",\"played\"))+\"<\/div>\"):e+=\"<p><b>Svi tiketi iz plana su prošli.<\/b><\/p>\";var i=o.tickets.filter(function(e){return e.done}).length;i&&(e+=\"<div>\"+k(\"Kopiraj odigrano (\"+i+\")\",\"copyplayed\")+\"<\/div>\")}else e+='<p style=\"color:#5a6678\">Nema učitanog plana.<\/p>';l.length&&(e+='<div style=\"margin-top:6px;padding:6px;background:#f4f6f9;border-radius:4px\">'+l.map(f).join(\"<br>\")+\"<\/div>\"),e+='<p style=\"color:#5a6678;font-size:12px;margin:8px 0 0\">Pomoćnik dodaje parove i upisuje ulog. Tiket proveri i uplati ti, dugmetom UPLATI, pa klikni Odigran.<\/p>',s.innerHTML=e}function b(e){var t=document.createElement(\"textarea\");t.value=e,t.style.cssText=\"width:100%25;height:80px;font:11px monospace\",s.appendChild(t),t.select()}var y=!1;function x(e){return new Promise(function(t){setTimeout(t,e)})}async function S(e,t){for(var a=Date.now();Date.now()-a<(t||8e3);){var n=e();if(n)return n;await x(150)}return null}function w(e){return!(!e||null===e.offsetParent)}function j(e){var t=String(e||\"\").replace(/[()\\s]/g,\"\").replace(\",\",\".\"),a=parseFloat(t);return isFinite(a)?a:null}function P(e){return String(e&&e.textContent||\"\").replace(/ /g,\" \").replace(/\\s+/g,\" \").trim()}function E(){return document.querySelectorAll(\"ds-content-ticket ds-ticket-match\").length}function O(e){return document.getElementById(e+\"-ticket\")}function q(){var e=[].slice.call(document.querySelectorAll(\"ds-match-special\")).filter(w);return e.length?e[e.length-1]:null}function A(e){for(var t=document.querySelectorAll(\"ion-grid.es-match\"),a=0;a<t.length;a++){var n=t[a].querySelectorAll(\".es-match-teams-item\");if(n.length&&u(n[0].textContent)===u(e))return t[a]}return null}async function M(){var e=q();if(!e)return!0;var t=e.querySelector(\"ion-button.back-button, .match-special--bck-btn\");return t?t.click():history.back(),!!await S(function(){return!q()&&w(document.querySelector(\"ion-grid.es-match\"))},7e3)}var T={P:\"poeni igraca\",S:\"skokovi igraca\",A:\"asistencije igraca\"},z={P:\"-\",S:\"SK-\",A:\"AS-\"},C={P:\"poeni\",S:\"skokovi\",A:\"asistencije\"};async function N(e,t){e.c,e.s;var a=null,n=null;if(O(e.c))return{ok:!1,msg:\"igrač je već na tiketu\"};if(\"P\"===e.s){if(q()&&!await M())return{ok:!1,msg:\"povratak na listu nije uspeo\"};var i=A(e.p);if(!i)return{ok:!1,msg:\"nije u ponudi\"};for(var r=i.querySelectorAll(\"button.odd-btn\"),o=0;o<r.length;o++){var l=r[o].getAttribute(\"title\")||\"\";if(/manje poena/i.test(l)&&!/alternat/i.test(l)){a=r[o];break}}if(!a)return{ok:!1,msg:\"dugme za manje nije nađeno\"};n=j(P(a.querySelector(\".odd-btn--special-value\")))}else{var s=q();if(!s||P(s.querySelector(\".match-special-teams\")).toLowerCase().indexOf(String(e.p).toLowerCase())<0){if(s&&!await M())return{ok:!1,msg:\"povratak na listu nije uspeo\"};var c=A(e.p);if(!c)return{ok:!1,msg:\"nije u ponudi\"};if(c.querySelector(\".es-match-teams-item\").click(),!(s=await S(function(){var t=q();return t&&P(t.querySelector(\".match-special-teams\")).toLowerCase().indexOf(String(e.p).toLowerCase())>=0&&t.querySelector(\"ds-match-special-group\")?t:null},9e3)))return{ok:!1,msg:\"stranica igrača se nije otvorila\"}}var p=await S(function(){for(var t=s.querySelectorAll(\"ds-match-special-group\"),a=0;a<t.length;a++){var n=t[a].querySelector(\".match-special-bet-pick-group\"),i=n&&n.querySelector(\"b\");if(u(P(n).replace(P(i),\"\"))===T[e.s])return t[a]}return null},6e3);if(!p)return{ok:!1,msg:\"kod igrača nema \"+C[e.s]};n=j(P(p.querySelector(\".match-special-bet-pick-group b\")));for(var d=p.querySelectorAll(\"button.odd-btn\"),f=0;f<d.length;f++)if(P(d[f].querySelector(\".odd-btn--tip\"))===z[e.s]){a=d[f];break}if(!a)return{ok:!1,msg:\"dugme za manje nije nađeno\"}}var g=j(P(a.querySelector(\".odd-btn--odd\")));if(null==n)return{ok:!1,msg:\"granica nije pročitana, dodaj ručno\"};if(n<e.l)return{ok:!1,msg:\"granica spuštena na \"+n+\", nije dodato\"};a.click();var m=await S(function(){return O(e.c)},4e3);if(!m)return{ok:!1,msg:\"klik nije prošao\"};var v=u(P(m.querySelector(\".ticket-match--group-name\")));if(v&&v.indexOf(C[e.s])<0)return{ok:!1,msg:\"na tiketu je druga igra (\"+P(m.querySelector(\".ticket-match--group-name\"))+\"), proveri\"};var k=[];return n>e.l&&k.push(\"granica podignuta na \"+n),g&&g!==e.u&&k.push(\"kvota \"+g),t.push({c:e.c,p:e.p,t:e.t||\"\",s:e.s,l:n,u:g||e.u}),{ok:!0,msg:k.join(\", \")}}}();";
  var BOOKMARKLET = "javascript:!function(){if(window.__mtPanel&&window.__mtVer===\"2\")window.__mtPanel.style.display=\"block\";else{if(window.__mtPanel){try{window.__mtPanel.remove()}catch(e){}window.__mtPanel=null}window.__mtVer=\"2\";var e=\"mt-admiral-plan\",t={\"ukupno poena\":\"P\",\"ukupno asistencija\":\"A\",\"ukupno skokova\":\"S\"},n={P:\"poeni\",A:\"asist.\",S:\"skokovi\"},a=\"https://feeds.incrowdsports.com/provider/euroleague-feeds/v3/competitions/E/statistics/\",i=\"https://api-live.euroleague.net/v2/competitions/E/seasons/\",o=function(){try{return JSON.parse(localStorage.getItem(e)||\"null\")}catch(e){return null}}(),r=!1,l=[],s=document.createElement(\"div\");window.__mtPanel=s,s.style.cssText=\"position:fixed;top:12px;right:12px;width:340px;max-height:88vh;overflow:auto;z-index:2147483647;background:#fff;color:#15223a;border:2px solid #d4470e;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.35);font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;padding:12px\",document.body.appendChild(s),s.addEventListener(\"click\",function(e){var t=e.target.closest(\"[data-a]\");if(t){var n=t.getAttribute(\"data-a\");if(\"close\"!==n)if(\"showplan\"!==n)if(\"loadplan\"!==n)if(\"lines\"!==n){if(\"offer\"===n){var r=function(){var e=d(),t=m(e),n=[];return e.querySelectorAll(\"app-event-with-selections\").forEach(function(e){var a=c((e.querySelector(\".code\")||{}).textContent),i=((e.querySelector(\".home\")||{}).textContent||\"\").trim(),o=((e.querySelector(\".away\")||{}).textContent||\"\").trim(),r=((e.querySelector(\".time\")||{}).textContent||\"\").trim();i&&e.querySelectorAll(\".col2 .bet-type-col\").forEach(function(e,l){var s=t[l];if(s){var u=e.querySelector('[data-market=\"manje\"]'),c=e.querySelector('[data-market=\"vise\"]');if(u&&!/locked|disabled/.test(u.className)){var d=e.querySelector(\".sbv [title]\"),m=p(d?d.getAttribute(\"title\"):(e.querySelector(\".sbv\")||{}).textContent),f=p(u.textContent),v=c&&!/locked|disabled/.test(c.className)?p(c.textContent):null;null!=m&&f&&n.push({c:a,p:i,t:o,s:s,l:m,u:f,o:v,time:r})}}})}),n}();return r.length?(l=[\"Preuzimam statistiku i raspored sa Evrolige…\"],S(),void async function(e){var t=new Date,n=t.getMonth()>=6?t.getFullYear():t.getFullYear()-1,o=\"E\"+n,r=\"E\"+(n-1),l=function(e){return g(e+\"&phaseTypeCode=RS\").then(function(t){return t.players&&t.players.length||t.teams&&t.teams.length?t:g(e)},function(){return g(e)})},s=await Promise.all([l(a+\"players/traditional?seasonMode=Single&limit=3000&statisticMode=perGame&seasonCode=\"+o),g(i+o+\"/games\"),l(a+\"teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+o).catch(function(){return{teams:[]}}),g(a+\"teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+r).catch(function(){return{teams:[]}}),l(a+\"teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+o).catch(function(){return{teams:[]}}),g(a+\"teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=\"+r).catch(function(){return{teams:[]}})]),u={season:o,at:t.toISOString(),players:{},games:[],clubs:{},def:{cur:{},prev:{}},rosters:{},tmap:{}};(s[0].players||[]).forEach(function(e){var t=e.gamesPlayed||0;t&&(u.players[v(e.player.name)]=[t,Math.round(10*e.minutesPlayed)/10,e.pointsScored,e.totalRebounds,e.assists,String(e.player.team&&e.player.team.code||\"\").split(\";\").pop(),e.foulsCommited||0],u.perGame=!0)});var c=function(e){return e.twoPointersAttempted+e.threePointersAttempted+.44*e.freeThrowsAttempted-e.offensiveRebounds+e.turnovers};[[\"cur\",s[2],s[4]],[\"prev\",s[3],s[5]]].forEach(function(e){var t={};(e[2].teams||[]).forEach(function(e){t[e.team.code]=c(e)}),(e[1].teams||[]).forEach(function(n){var a=c(n),i=t[n.team.code]||a;u.def[e[0]][n.team.code]=[n.gamesPlayed,n.pointsScored,n.totalRebounds,n.assists,Math.round((a+i)/2*10)/10,Math.round(n.pointsScored/a*1e3)/10]})});var p=t.getTime()-432e5,d=t.getTime()+3456e5;(s[1].data||[]).forEach(function(e){var t=Date.parse(e.utcDate||e.date);t>=p&&t<=d&&!e.played&&([e.local.club,e.road.club].forEach(function(e){u.clubs[e.code]={name:e.name,abbr:e.abbreviatedName||\"\",ed:e.editorialName||\"\"}}),u.games.push({d:e.utcDate||e.date,h:e.local.club.code,a:e.road.club.code}))});var m={};e.forEach(function(e){m[e.t]=1}),Object.keys(m).forEach(function(e){var t=f(e).split(\" \"),n=null,a=0;Object.keys(u.clubs).forEach(function(e){var i=u.clubs[e],o=f(i.name+\" \"+i.abbr+\" \"+i.ed).split(\" \"),r=0;t.forEach(function(e){e.length>2&&o.indexOf(e)>=0&&(r+=e.length)}),r>a&&(a=r,n=e)}),n&&(u.tmap[e]=n)});var h=Object.keys(u.clubs);return await Promise.all(h.map(function(e){return g(i+o+\"/clubs/\"+e+\"/people\").then(function(t){u.rosters[e]=(t||[]).filter(function(e){return\"J\"===e.type&&!1!==e.active&&e.person}).map(function(e){return[v(e.person.name),e.positionName||\"\",e.person.name]})}).catch(function(){})})),u}(r).then(function(e){return{el:e,err:\"\"}},function(e){return{el:null,err:e&&e.message||\"greška\"}}).then(function(e){var t=JSON.stringify({v:2,src:\"admiralbet\",at:(new Date).toISOString(),picks:r,el:e.el}),n=e.el?\"Statistika preuzeta: \"+Object.keys(e.el.players).length+\" igrača, \"+e.el.games.length+\" utakmica.\":\"Statistika sa Evrolige nije preuzeta (\"+e.err+\"), kopirana je samo ponuda.\";j(t).then(function(e){if(l=[n,e?\"Ponuda kopirana (\"+r.length+\" linija). Nalepi je u aplikaciju, na kartici Generator.\":\"Kopiranje nije uspelo. Označi tekst ispod i kopiraj ga ručno.\"],S(),!e){var a=document.createElement(\"textarea\");a.value=t,a.style.cssText=\"width:100%;height:80px;font:11px monospace\",s.appendChild(a),a.select()}})})):(l=[\"Ponuda nije pronađena. Otvori Košarka igrači, Igrači ukupno, Evroliga.\"],void S())}if(o)if(\"build\"!==n){if(\"unbuild\"===n){var u=o.tickets[o.idx||0];return u&&(u.built=!1,u.actual=null),y(o),void S()}if(\"played\"!==n)return\"next\"===n?(o.idx=Math.min((o.idx||0)+1,o.tickets.length),l=[],y(o),void S()):\"prev\"===n?(o.idx=Math.max((o.idx||0)-1,0),l=[],y(o),void S()):void 0;var h=o.tickets.filter(function(e){return e.built&&e.actual&&e.actual.length}).map(function(e){return{stake:e.stake,legs:e.actual}}),k=JSON.stringify({v:1,kind:\"played\",round:o.round||\"\",at:(new Date).toISOString(),tickets:h});j(k).then(function(e){if(l=[e?\"Kopirano \"+h.length+\" odigranih tiketa.\":\"Kopiranje nije uspelo. Označi tekst ispod i kopiraj ga ručno.\"],S(),!e){var t=document.createElement(\"textarea\");t.value=k,t.style.cssText=\"width:100%;height:80px;font:11px monospace\",s.appendChild(t),t.select()}})}else w()}else{var b=function(){var e=d(),t=e.querySelector(\".bet-type-name-wrap\"),n=(t?Array.prototype.map.call(t.querySelectorAll(\".bet-type-col\"),function(e){return c(e.textContent)}):[]).map(function(e){return/poena|asistencij|skokov/.test(e)?null:/domacin|domaćin/.test(e)&&/ukupno/.test(e)?\"hTot\":/gost/.test(e)&&/ukupno/.test(e)?\"aTot\":/ukupno/.test(e)?\"total\":/pobednik/.test(e)?\"ml\":null}),a=[];return e.querySelectorAll(\"app-event-with-selections\").forEach(function(e){var t=((e.querySelector(\".home\")||{}).textContent||\"\").trim(),i=((e.querySelector(\".away\")||{}).textContent||\"\").trim();if(t&&i){var o={home:t,away:i,time:((e.querySelector(\".time\")||{}).textContent||\"\").trim()};e.querySelectorAll(\".col2 .bet-type-col\").forEach(function(e,t){var a=n[t];if(a)if(\"ml\"!==a){var i=e.querySelector(\".sbv [title]\"),r=p(i?i.getAttribute(\"title\"):(e.querySelector(\".sbv\")||{}).textContent);null!=r&&(o[a]=r)}else{var l=e.querySelectorAll(\"[data-market]\");l.length>=2&&(o.ml1=p(l[0].textContent),o.ml2=p(l[l.length-1].textContent))}}),null==o.total&&null==o.hTot&&null==o.aTot||a.push(o)}}),a}();if(!b.length)return l=[\"Kvote utakmica nisu pronađene. Otvori glavnu ponudu Evrolige, gde se vide kolone Ukupno i Domaćin ili Gost ukupno.\"],void S();var x=JSON.stringify({v:1,kind:\"lines\",at:(new Date).toISOString(),games:b});j(x).then(function(e){if(l=[e?\"Kopirane kvote za \"+b.length+\" utakmica. Nalepi ih u aplikaciju, Generator, deo Kvote utakmica. Ako vidiš samo Domaćin ukupno, prebaci na Gost ukupno i kopiraj još jednom.\":\"Kopiranje nije uspelo. Označi tekst ispod i kopiraj ga ručno.\"],S(),!e){var t=document.createElement(\"textarea\");t.value=x,t.style.cssText=\"width:100%;height:80px;font:11px monospace\",s.appendChild(t),t.select()}})}else{try{var E=JSON.parse(s.querySelector(\"#mt-plan\").value.trim());if(!E||!Array.isArray(E.tickets)||!E.tickets.length)throw 0;E.idx=0,y(o=E),l=[\"Plan učitan: \"+E.tickets.length+\" tiketa.\"]}catch(e){l=[\"Plan nije ispravan. Kopiraj ga ponovo iz aplikacije.\"]}S()}else{var q=s.querySelector(\"#mt-planbox\");q.style.display=\"none\"===q.style.display?\"block\":\"none\"}else s.style.display=\"none\"}}),S()}function u(e){return new Promise(function(t){setTimeout(t,e)})}function c(e){return String(e||\"\").replace(/\\s+/g,\" \").trim().toLowerCase()}function p(e){var t=parseFloat(String(e||\"\").replace(\",\",\".\"));return isFinite(t)?t:null}function d(){var e=document.getElementById(\"sportIframe\");try{if(e&&e.contentDocument&&e.contentDocument.querySelector(\"app-event-with-selections, app-ticket\"))return e.contentDocument}catch(e){}return document}function m(e){var n=e.querySelector(\".bet-type-name-wrap\");return n?Array.prototype.map.call(n.querySelectorAll(\".bet-type-col\"),function(e){return t[c(e.textContent)]||null}):[\"P\",\"A\",\"S\"]}function f(e){var t=String(e||\"\").normalize(\"NFD\").replace(/[\\u0300-\\u036f]/g,\"\").toLowerCase().replace(/đ/g,\"dj\");return(t=t.replace(/\\b([a-z])\\.\\s*([a-z])\\./g,\"$1$2\").replace(/[-.]/g,\" \").replace(/[^a-z ]/g,\"\")).split(/\\s+/).filter(function(e){return e&&[\"jr\",\"sr\",\"ii\",\"iii\",\"iv\"].indexOf(e)<0}).join(\" \")}function v(e){if(e.indexOf(\",\")>=0){var t=e.split(\",\");return f(t[1]+\" \"+t[0])}return f(e)}async function g(e){var t=await fetch(e,{credentials:\"omit\"});if(!t.ok)throw new Error(\"HTTP \"+t.status);return t.json()}function h(e,t,n){for(var a=e.querySelectorAll(\"app-event-with-selections\"),i=null,o=0;o<a.length;o++){var r=c((a[o].querySelector(\".code\")||{}).textContent),l=c((a[o].querySelector(\".home\")||{}).textContent);if(n.c&&r===String(n.c)||!n.c&&l===c(n.p)){i=a[o];break}}if(!i)return null;var s=i.querySelectorAll(\".col2 .bet-type-col\")[t.indexOf(n.s)];if(!s)return null;var u=s.querySelector(\".sbv [title]\");return{u:s.querySelector(n.d===\"O\"?'[data-market=\"vise\"]':'[data-market=\"manje\"]'),line:p(u?u.getAttribute(\"title\"):(s.querySelector(\".sbv\")||{}).textContent)}}function k(e){return e.querySelectorAll(\"app-ticket .ticket-item\").length}function y(t){try{localStorage.setItem(e,JSON.stringify(t))}catch(e){}}function b(e,t,n){return'<button data-a=\"'+t+'\" style=\"margin:3px 4px 3px 0;padding:6px 10px;border-radius:4px;cursor:pointer;font:inherit;font-weight:600;border:1px solid '+(n?\"#d4470e;background:#d4470e;color:#fff\":\"#b8c0cc;background:#f4f6f9;color:#15223a\")+'\">'+e+\"</button>\"}function x(e){return String(null==e?\"\":e).replace(/[&<>\"]/g,function(e){return{\"&\":\"&amp;\",\"<\":\"&lt;\",\">\":\"&gt;\",'\"':\"&quot;\"}[e]})}function S(){var e='<div style=\"display:flex;justify-content:space-between;align-items:center\"><b style=\"font-size:15px\">Admiral pomoćnik v2 (minusi i plusevi)</b>'+b(\"×\",\"close\")+\"</div>\";if(e+=\"<div>\"+b(\"Kopiraj ponudu i statistiku\",\"offer\")+b(\"Kopiraj kvote utakmica\",\"lines\")+b(\"Nalepi plan\",\"showplan\")+\"</div>\",e+='<div id=\"mt-planbox\" style=\"display:none\"><textarea id=\"mt-plan\" style=\"width:100%;height:80px;font:11px monospace\" placeholder=\"Nalepi plan iz aplikacije\"></textarea>'+b(\"Učitaj plan\",\"loadplan\",!0)+\"</div>\",o&&o.tickets&&o.tickets.length){var t=o.idx||0,a=o.tickets[t];e+='<div style=\"margin-top:8px;padding-top:8px;border-top:1px solid #ddd\">Plan: <b>'+o.tickets.length+\" tiketa</b>\"+(o.round?\", kolo \"+x(o.round):\"\")+\"</div>\",a?(e+='<div style=\"margin:6px 0\"><b>Tiket '+(t+1)+\" od \"+o.tickets.length+\"</b>, ulog \"+x(a.stake)+\" din, \"+a.legs.length+\" parova</div>\",e+='<ol style=\"margin:0 0 6px;padding-left:20px\">'+a.legs.map(function(e){var t=(a.marks||{})[e.c+e.s];return\"<li>\"+(t?'<span style=\"color:'+(t.ok?\"#1d7a4b\":\"#b2261e\")+'\">'+(t.ok?\"✓ \":\"✗ \")+\"</span>\":\"\")+x(e.p)+\", \"+n[e.s]+(e.d===\"O\"?\" PREKO \":\" ispod \")+e.l+\" @ \"+e.u+(t&&t.msg?' <i style=\"color:'+(t.ok?\"#8a6d00\":\"#b2261e\")+'\">'+x(t.msg)+\"</i>\":\"\")+\"</li>\"}).join(\"\")+\"</ol>\",e+='<div style=\"display:flex;gap:6px\">'+b(\"‹ Prethodni\",\"prev\")+b(\"Sledeći ›\",\"next\")+\"</div>\",e+=\"<div>\"+b(r?\"Slažem…\":\"Složi tiket \"+(t+1),\"build\",!0).replace('style=\"','style=\"width:100%;padding:10px;font-size:14px;')+\"</div>\"):e+=\"<p><b>Svi tiketi iz plana su prošli.</b></p>\";var i=o.tickets.filter(function(e){return e.built}).length,u=o.tickets[o.idx||0];(i||u&&u.built)&&(e+='<div style=\"display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-top:2px\">'+(u&&u.built?b(\"Nisam uplatio\",\"unbuild\"):\"\")+(i?b(\"Kopiraj odigrano (\"+i+\")\",\"played\"):\"\")+\"</div>\"+(u&&u.built?'<div style=\"color:#1d7a4b;font-size:12px\">Tiket '+((o.idx||0)+1)+\" je složen. Ako ga ne uplatiš, klikni „Nisam uplatio“.</div>\":\"\"))}else e+='<p style=\"color:#5a6678\">Nema učitanog plana. Napravi plan u aplikaciji i nalepi ga ovde.</p>';l.length&&(e+='<div style=\"margin-top:6px;padding:6px;background:#f4f6f9;border-radius:4px\">'+l.map(x).join(\"<br>\")+\"</div>\"),e+='<p style=\"color:#5a6678;font-size:12px;margin:8px 0 0\">Pomoćnik samo bira parove i upisuje ulog. Tiket proveri i uplati ti, dugmetom UPLATA.</p>',s.innerHTML=e}function j(e){return navigator.clipboard&&navigator.clipboard.writeText?navigator.clipboard.writeText(e).then(function(){return!0},function(){return t()}):Promise.resolve(t());function t(){var t=document.createElement(\"textarea\");t.value=e,t.style.cssText=\"position:fixed;left:-9999px\",document.body.appendChild(t),t.select();var n=!1;try{n=document.execCommand(\"copy\")}catch(e){}return t.remove(),n}}async function w(){if(!r){r=!0,l=[],S();var e=d(),t=m(e),n=o.tickets[o.idx||0];n.marks={};try{if(!e.querySelector(\"app-event-with-selections\"))throw new Error(\"Na ovoj stranici nema ponude. Otvori Košarka igrači, Igrači ukupno, Evroliga.\");if(k(e)){var a=e.querySelector(\"app-ticket .empty-ticket\");if(a&&a.click(),await u(700),k(e))throw new Error(\"Tiket nije prazan. Obriši ga ručno (BRIŠI TIKET) pa klikni ponovo.\")}for(var i=0,s=[],c=0;c<n.legs.length;c++){var f=n.legs[c],v=h(e,t,f),g=f.c+f.s;if(v&&v.u&&!/locked|disabled/.test(v.u.className))if(null!=v.line)if(f.d===\"O\"?v.line>f.l:v.line<f.l)n.marks[g]={ok:!1,msg:\"linija je pomerena na \"+v.line+\", nije dodato, proveri ručno\"},l.push(f.p+\": linija pomerena sa \"+f.l+\" na \"+v.line+\", par nije dodat.\");else{var b=k(e);/\\bselected\\b/.test(v.u.className)||(v.u.click(),await u(450));var x=/\\bselected\\b/.test(v.u.className)||k(e)>b,j=p(v.u.textContent),w=[];x&&v.line!==f.l&&w.push(\"linija \"+v.line),x&&j&&j!==f.u&&w.push(\"kvota \"+j),n.marks[g]=x?{ok:!0,msg:w.join(\", \")}:{ok:!1,msg:\"klik nije prošao\"},x&&(i++,s.push({c:f.c,p:f.p,t:f.t||\"\",s:f.s,l:v.line,u:j||f.u,d:f.d||\"\"}),v.line!==f.l&&l.push(f.p+\": linija promenjena sa \"+f.l+\" na \"+v.line+\", par je dodat.\"),j&&j!==f.u&&l.push(f.p+\": kvota je sada \"+j+\" (u planu \"+f.u+\").\")),S()}else n.marks[g]={ok:!1,msg:\"linija nije pročitana, proveri ručno\"};else n.marks[g]={ok:!1,msg:\"nije u ponudi\"}}await u(300),n.actual=s,n.built=i>0;var E=function(e,t){var n=e.getElementById(\"totalStakeInput\");if(!n)return!1;var a=Object.getOwnPropertyDescriptor(Object.getPrototypeOf(n),\"value\");return n.focus(),a&&a.set?a.set.call(n,String(t)):n.value=String(t),[\"input\",\"change\",\"keyup\"].forEach(function(e){n.dispatchEvent(new Event(e,{bubbles:!0}))}),n.blur(),n.dispatchEvent(new Event(\"blur\",{bubbles:!0})),!0}(e,n.stake);l.unshift(\"Dodato \"+i+\" od \"+n.legs.length+\" parova. Na tiketu: \"+k(e)+\".\"),E?l.push(\"Ulog \"+n.stake+\" din je upisan. Proveri tiket i klikni UPLATA.\"):l.push(\"Polje za ulog nije pronađeno, upiši ulog ručno.\"),i<n.legs.length&&l.push(\"Neki parovi nisu dodati. Proveri ih: možeš ih dodati ručno pre uplate ili igrati tiket bez njih. Ručno dodate parove posle ispravi u aplikaciji.\");var q=e.querySelector(\"app-ticket .place-bet-wrap .btn.primary\");q&&function(e,t){t.style.outline=\"3px solid #d4470e\",t.style.outlineOffset=\"2px\";var n=document.getElementById(\"sportIframe\");try{if(e!==document&&n){var a=t.getBoundingClientRect(),i=n.getBoundingClientRect(),o=window.pageYOffset+i.top+a.top+a.height/2-window.innerHeight/2;window.scrollTo({top:Math.max(0,o),behavior:\"smooth\"})}else t.scrollIntoView({block:\"center\",behavior:\"smooth\"})}catch(e){}setTimeout(function(){try{t.focus({preventScroll:!0})}catch(e){try{t.focus()}catch(e){}}},450)}(e,q)}catch(e){l.push(e.message||String(e))}r=!1,y(o),S()}}}();";
  function deacc(s){ return String(s || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/g, 'dj').replace(/Đ/g, 'Dj').toLowerCase().replace(/\s+/g, ' ').trim(); }
  function getOffer(){
    var loc = null;
    try { loc = JSON.parse(localStorage.getItem('mt-offer') || 'null'); } catch(e) {}
    var seed = state.offer || null;
    if (loc && loc.picks && (!seed || String(loc.at) >= String(seed.at))) return loc;
    return seed;
  }
  function genCfg(){
    if (!ui.gen) ui.gen = {total: '2000', round: '', stats: {P: true, A: true, S: true}, onlyPos: false, excl: {}};
    var g = ui.gen;
    if (!g.mix) g.mix = [{legs: String(g.legs || '8'), n: String(g.n || '20')}];
    if (g.maxUse == null) g.maxUse = '5';
    if (g.balance == null) g.balance = true;
    if (g.strong == null) g.strong = true;
    if (g.maxTeam == null) g.maxTeam = '2';
    if (g.minOdds == null) g.minOdds = '';
    if (g.maxOdds == null) g.maxOdds = '';
    if (!g.forced) g.forced = {};
    if (g.stackN == null) g.stackN = '0';
    if (g.focus == null) g.focus = 'sansa';
    if (g.rot == null) g.rot = true;
    if (g.maxPl == null) g.maxPl = '50';
    if (g.opt == null) g.opt = true;
    if (g.minCov == null) g.minCov = '2';
    if (g.gameShare == null) g.gameShare = '50';
    if (!g.v3) { g.v3 = true; if (!g.maxPl || g.maxPl === '50') g.maxPl = '20'; if (!g.maxUse || +g.maxUse < 6) g.maxUse = '6'; }
    if (!g.pref) g.pref = {};
    if (g.needAbove == null) g.needAbove = true;
    if (!g.v2) { g.v2 = true; if (!g.minOdds) g.minOdds = '1.70'; }
    if (g.stackK == null) g.stackK = '4';
    if (!g.excl) g.excl = {};
    if (!g.stats) g.stats = {P: true, A: true, S: true};
    if (g.best == null) g.best = false;
    if (!g.v5) { g.v5 = true; g.best = false; }
    // provera posle 7. kola: parovi sa najviše ponavljanja prolazili su lošije od ostalih, pa ★ ne dobija dodatna ponavljanja dok nova procena ne potvrdi da ih zaslužuje
    if (!g.v6) { g.v6 = true; g.strong = false; }
    // od 28.10.2026: najmanja kvota 1,65 (Nikola), parovi ispod 1,70 raspoređeni najviše po jedan na tiketu
    if (!g.v7) { g.v7 = true; if (!g.minOdds || g.minOdds === '1.70') g.minOdds = '1.65'; }
    if (!g.v4) { g.v4 = true; g.maxUse = ''; g.rot = true; g.opt = true; }
    return g;
  }
  var PRESETS = {
    stil: {label: 'Tvoj uobičajeni stil', desc: '10 tiketa po 8, 6 po 9 i 4 po 10 parova, 2.000 din, igrač najviše na 5 tiketa, najviše 2 igrača iz istog tima.', set: {mix: [{legs:'8', n:'10'}, {legs:'9', n:'6'}, {legs:'10', n:'4'}], total: '2000', maxUse: '5', maxTeam: '2', balance: true, strong: true, minOdds: '1.65', maxOdds: '', onlyPos: false, stats: {P:true, A:true, S:true}}},
    manje: {label: 'Kraći tiketi', desc: '10 tiketa po 4 para i 10 po 5 parova, 2.000 din. Tiket prolazi mnogo češće, a dobici su manji.', set: {mix: [{legs:'4', n:'10'}, {legs:'5', n:'10'}], total: '2000', maxUse: '6', maxTeam: '2', balance: true, strong: true, minOdds: '1.65', maxOdds: '', onlyPos: false, stats: {P:true, A:true, S:true}}},
    poeni: {label: 'Samo poeni', desc: '15 tiketa po 8 parova, samo minusi za poene, kvota od 1,85 naviše, 1.500 din.', set: {mix: [{legs:'8', n:'15'}], total: '1500', maxUse: '5', maxTeam: '2', balance: true, strong: true, minOdds: '1.85', maxOdds: '', onlyPos: false, stats: {P:true, A:false, S:false}}},
    rasprseno: {label: 'Najveće rasipanje', desc: '20 tiketa po 8 parova, igrač najviše na 3 tiketa, najviše 2 igrača iz istog tima i bez dodatnih ponavljanja za ★ izbore. Jedan promašaj obara najmanje tiketa.', set: {mix: [{legs:'8', n:'20'}], total: '2000', maxUse: '3', maxTeam: '2', balance: true, strong: false, minOdds: '1.65', maxOdds: '', onlyPos: false, stats: {P:true, A:true, S:true}}}
  };
  function minBucket(name){ var e = avgLookup(name); var pm = e && e.c ? e.c[1] : null; if (pm == null) return 'nov'; return pm < 15 ? 'm0' : pm < 20 ? 'm15' : pm < 25 ? 'm20' : 'm25'; }
  function oddsBucket2(u){ return u < 1.7 ? 'o1' : u < 1.85 ? 'o2' : u < 1.95 ? 'o3' : 'o4'; }
  function histMaps(){
    var m = {ps: {}, ts: {}, st: {}, mb: {}, ob: {}, tt: {}};
    settledPicks(true).forEach(function(e){
      [['ps', deacc(e.p) + '|' + e.stat], ['ts', deacc(e.team) + '|' + e.stat], ['st', e.stat], ['mb', minBucket(e.p)], ['ob', oddsBucket2(e.avgOdds)], ['tt', deacc(e.team)]].forEach(function(x){
        var g = m[x[0]][x[1]] || (m[x[0]][x[1]] = {n: 0, h: 0, be: 0});
        g.n++; if (e.status === 'hit') g.h++; g.be += 1 / e.avgOdds;
      });
    });
    return m;
  }
  function dEdge(g, k){ return g && g.n ? g.n / (g.n + k) * (g.h / g.n - g.be / g.n) : 0; }
  function nkey(v){
    var t = String(v || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().replace(/đ/g, 'dj');
    t = t.replace(/\b([a-z])\.\s*([a-z])\./g, '$1$2').replace(/[-.]/g, ' ').replace(/[^a-z ]/g, '');
    return t.split(/\s+/).filter(function(w){ return w && ['jr','sr','ii','iii','iv'].indexOf(w) < 0; }).join(' ');
  }
  var AVG_IDX = null;
  function keyMatch(map, keys, k){
    if (map[k]) return map[k];
    var t = k.split(' '); if (!t[0]) return null;
    var c = keys.filter(function(kk){ var q = kk.split(' '); return q[q.length - 1] === t[t.length - 1] && q[0][0] === t[0][0]; });
    return c.length === 1 ? map[c[0]] : null;
  }
  var INJ_IDX = null;
  var INJ_TXT = {out: 'ne igra', doubtful: 'upitan', dtd: 'odluka pred utakmicu'};
  function injuryOf(name){
    var I = state.injuries; if (!I || !I.list) return null;
    if (!INJ_IDX || INJ_IDX.src !== I) { var m = {}; I.list.forEach(function(r){ m[nkey(r.p)] = r; }); INJ_IDX = {src: I, m: m, keys: Object.keys(m)}; }
    return keyMatch(INJ_IDX.m, INJ_IDX.keys, nkey(name));
  }
  function avgLookupK(k){
    if (!AVG_IDX) { var db = (state.avg && state.avg.db) || {}; AVG_IDX = {db: db, keys: Object.keys(db)}; }
    return keyMatch(AVG_IDX.db, AVG_IDX.keys, k);
  }
  function avgLookup(name){ return avgLookupK(nkey(name)); }
  var EL_IDX = null;
  function elCtx(){ var off = getOffer(); return off && off.el ? off.el : null; }
  function normCur(r){
    if (!r) return null;
    var pf = typeof r[5] === 'string' ? (r[6] || 0) : (r[5] || 0);
    return [r[0], r[1], r[2], r[3], r[4], pf];
  }
  function curStatsK(k){
    var el = elCtx();
    if (el && el.players) {
      if (!EL_IDX || EL_IDX.el !== el) EL_IDX = {el: el, keys: Object.keys(el.players)};
      var r = keyMatch(el.players, EL_IDX.keys, k);
      if (r) return normCur(r);
      if (el.perGame) return null;
    }
    var e = avgLookupK(k); return e && e.s ? normCur(e.s) : null;
  }
  function expMinK(k){ var c = curStatsK(k); if (c) return c[1]; var e = avgLookupK(k); return e && e.c ? e.c[1] : null; }
  function avgFor(name, stat){
    var k = nkey(name), e = avgLookupK(k), ix = {P: 2, S: 3, A: 4}[stat], cs = curStatsK(k), prior = e && e.c ? e.c : null;
    if (!prior && !cs) return null;
    var cur = cs ? {v: cs[ix], g: cs[0], min: cs[1], pf: cs[5] || 0} : null, car = null;
    if (prior) {
      var gp = prior[0];
      if (cs) { var gt = gp + cs[0]; car = {v: (prior[ix] * gp + cs[ix] * cs[0]) / gt, g: gt, min: (prior[1] * gp + cs[1] * cs[0]) / gt}; }
      else car = {v: prior[ix], g: gp, min: prior[1]};
    }
    var wcur = 0, rate = null, minP = null, foul = false;
    if (cur && prior && cur.min > 0 && prior[1] > 0) {
      wcur = cur.g / (cur.g + 4);
      rate = wcur * (cur.v / cur.min) + (1 - wcur) * (prior[ix] / prior[1]);
      var w2 = cur.g / (cur.g + 2);
      foul = cur.g <= 3 && cur.pf / cur.g >= 4 && cur.min < prior[1] - 1;
      if (foul) w2 *= 0.2;
      minP = w2 * cur.min + (1 - w2) * prior[1];
    } else if (cur && cur.min > 0) {
      wcur = 1; rate = cur.v / cur.min; minP = cur.min;
      foul = cur.g <= 3 && cur.pf / cur.g >= 4 && cur.min < 24;
      if (foul) minP = Math.min(30, cur.min * 1.25);
    } else if (prior && prior[1] > 0) { rate = prior[ix] / prior[1]; minP = prior[1]; }
    var dec = rate != null ? rate * minP : (cur ? cur.v : prior ? prior[ix] : null);
    return {car: car, cur: cur, v: dec, wcur: wcur, minP: minP, foul: foul};
  }
  function prettyName(raw){
    if (!raw) return '';
    var q = raw.indexOf(',') >= 0 ? raw.split(',') : [raw, ''];
    var nm = (String(q[1]).trim() + ' ' + String(q[0]).trim()).trim().toLowerCase();
    return nm.replace(/(^|[\s-])([a-zà-ž])/g, function(m, a, b){ return a + b.toUpperCase(); });
  }
  var CTX_CACHE = null;
  function schedEl(off){
    var S = state.sched; if (!S || !S.games || !off || !off.picks) return null;
    var tm = {}, teams = {};
    off.picks.forEach(function(x){ teams[x.t] = 1; });
    Object.keys(teams).forEach(function(tn){
      var tk = nkey(tn).split(' '), best = null, bs = 0;
      Object.keys(S.clubs).forEach(function(code){
        var c = S.clubs[code], words = nkey(c.name + ' ' + (c.abbr || '')).split(' '), sc2 = 0;
        tk.forEach(function(w){ if (w.length > 2 && words.indexOf(w) >= 0) sc2 += w.length; });
        if (sc2 > bs) { bs = sc2; best = code; }
      });
      if (best) tm[tn] = best;
    });
    return {tmap: tm, games: S.games, clubs: S.clubs, def: state.teamStats || {cur: {}, prev: {}}, rosters: {}, fallback: true};
  }
  function ctx(){
    var off = getOffer(), el = off && off.el; if (!el || !el.tmap) el = schedEl(off); if (!el) return null;
    var g = genCfg(), sig = (off.at || '') + '|' + JSON.stringify(g.absOff || {}) + '|' + JSON.stringify(g.absMan || {});
    if (CTX_CACHE && CTX_CACHE.sig === sig) return CTX_CACHE;
    var C = {sig: sig, el: el, opp: {}, pos: {}, absent: {}, cand: [], boost: {}, boostPos: {}, posWho: {}, absWho: {}, allowed: {}, league: [0, 0, 0]};
    (el.games || []).slice().sort(function(a, b){ return String(a.d).localeCompare(String(b.d)); }).forEach(function(gm){ if (!C.opp[gm.h]) C.opp[gm.h] = gm.a; if (!C.opp[gm.a]) C.opp[gm.a] = gm.h; });
    var dc = (el.def && el.def.cur) || {}, dp = (el.def && el.def.prev) || {}, codes = {};
    Object.keys(dc).forEach(function(k){ codes[k] = 1; }); Object.keys(dp).forEach(function(k){ codes[k] = 1; });
    Object.keys(codes).forEach(function(k){
      var c = dc[k], q = dp[k], r = [0, 0, 0];
      for (var i = 0; i < 3; i++) r[i] = c && q ? (c[0] / (c[0] + 6)) * c[i + 1] + (1 - c[0] / (c[0] + 6)) * q[i + 1] : (c || q)[i + 1];
      C.allowed[k] = r;
    });
    var ks = Object.keys(C.allowed);
    ks.forEach(function(k){ for (var i = 0; i < 3; i++) C.league[i] += C.allowed[k][i] / ks.length; });
    C.pace = {}; C.drtg = {}; C.lgPace = 0; C.lgDrtg = 0;
    var tsc = (state.teamStats && state.teamStats.cur) || {}, tsp = (state.teamStats && state.teamStats.prev) || {};
    Object.keys(codes).forEach(function(k){
      var c = dc[k] && dc[k].length > 5 ? dc[k] : tsc[k], q = dp[k] && dp[k].length > 5 ? dp[k] : tsp[k];
      if (!c && !q) return;
      var w = c && q ? c[0] / (c[0] + 6) : (c ? 1 : 0);
      C.pace[k] = c && q ? w * c[4] + (1 - w) * q[4] : (c || q)[4];
      C.drtg[k] = c && q ? w * c[5] + (1 - w) * q[5] : (c || q)[5];
    });
    var pk3 = Object.keys(C.pace);
    pk3.forEach(function(k){ C.lgPace += C.pace[k] / pk3.length; C.lgDrtg += C.drtg[k] / pk3.length; });
    var inOffer = {}; off.picks.forEach(function(pk){ inOffer[nkey(pk.p)] = 1; });
    var offLast = {}; off.picks.forEach(function(pk){ var cc = el.tmap[pk.t], t = nkey(pk.p).split(' '); if (cc) (offLast[cc] = offLast[cc] || {})[t[t.length - 1]] = 1; });
    var offKeys = Object.keys(inOffer), isOffered = function(k, code){ if (keyMatch(inOffer, offKeys, k)) return true; var t = k.split(' '); return !!(offLast[code] && offLast[code][t[t.length - 1]]); };
    Object.keys(el.rosters || {}).forEach(function(code){ (el.rosters[code] || []).forEach(function(r){ C.pos[r[0]] = r[1]; }); });
    var clubs = {}; Object.keys(el.tmap).forEach(function(t){ clubs[el.tmap[t]] = 1; });
    g.absOff = g.absOff || {}; g.absMan = g.absMan || {};
    Object.keys(clubs).forEach(function(code){
      var present = [], absent = [], teamGp = 0;
      (el.rosters[code] || []).forEach(function(r){ var cs0 = curStatsK(r[0]); if (cs0 && cs0[0] > teamGp) teamGp = cs0[0]; });
      (el.rosters[code] || []).forEach(function(r){
        var k = r[0], m = expMinK(k); if (m == null) return;
        var ij = injuryOf(prettyName(r[2])), offered = isOffered(k, code), ijOut = ij && ij.s === 'out', ijQ = ij && (ij.s === 'doubtful' || ij.s === 'dtd');
        // igrač koji je u ponudi verovatno igra, čak i ako ga stari izveštaj vodi kao povređenog; igrač kog nema u ponudi računa se kao odsutan sa manjom težinom, jer kladionica ne nudi sve igrače
        // kladionica ne nudi igrače koji daju malo poena (npr. Weiler-Babb, oko 2 poena za 20 minuta), pa njihov izostanak iz ponude ne znači da ne igraju
        var csLow = curStatsK(k), lowScorer = !!(csLow && csLow[0] >= 3 && csLow[2] < 5);
        var auto = (!offered && m >= 18 && !lowScorer) || (ijOut && !offered), man = !!g.absMan[k], out = (auto && !g.absOff[k]) || man;
        if (auto || man || (ijQ && m >= 12) || (ijOut && offered)) C.cand.push({k: k, name: prettyName(r[2]), club: code, m: m, pos: r[1], on: out, auto: auto, inj: ij ? ij.s : '', why: ijOut && offered ? 'izveštaj kaže da ne igra, ali je u ponudi kladionice' : ijOut ? 'izveštaj o povredama: ne igra' : ij && ijQ ? 'izveštaj o povredama: ' + INJ_TXT[ij.s] + (offered ? '' : ', nema ga u ponudi') : (!offered ? 'nema ga u ponudi' : 'dodato ručno')});
        if (out) {
          var csA = curStatsK(k), share = teamGp ? Math.max(0.15, Math.min(1, (csA ? csA[0] : 0) / teamGp)) : 1;
          // ako je igrač propustio deo sezone, saigrači već imaju te minute u prosecima; računa se samo deo koji nije uračunat
          absent.push({k: k, m: m, pos: r[1], name: prettyName(r[2]), w: (man || ijOut || (ijQ && !offered) ? 1 : 0.4) * share}); C.absent[k] = true;
        }
        else if (m >= 8) present.push({k: k, m: m, pos: r[1]});
      });
      var extra = {}, extraPos = {}, posWho = {};
      absent.forEach(function(a){
        var ws = present.map(function(x){ return x.m * (x.pos && x.pos === a.pos ? 2 : 1); }), sum = ws.reduce(function(x, y){ return x + y; }, 0);
        if (!sum) return;
        present.forEach(function(x, i){ var e = 0.8 * a.m * (a.w || 1) * ws[i] / sum; extra[x.k] = (extra[x.k] || 0) + e; if (x.pos && x.pos === a.pos) { extraPos[x.k] = (extraPos[x.k] || 0) + e; (posWho[x.k] = posWho[x.k] || []).push(a.name); } });
      });
      present.forEach(function(x){ C.boost[x.k] = Math.min(1.4, (x.m + (extra[x.k] || 0)) / x.m); C.boostPos[x.k] = (extraPos[x.k] || 0) / x.m; C.posWho[x.k] = posWho[x.k] || []; });
      C.absWho[code] = absent.map(function(a){ return a.name; });
    });
    CTX_CACHE = C; return C;
  }
  function clubsList(){ var C = ctx(); if (C && C.el && C.el.clubs) return C.el.clubs; return (state.sched && state.sched.clubs) || {}; }
  function codeByName(name, clubs){
    var tk = nkey(name).split(' '), best = null, bs = 0;
    Object.keys(clubs).forEach(function(code){
      var c = clubs[code], words = nkey((c.name || '') + ' ' + (c.abbr || '') + ' ' + (c.ed || '')).split(' '), sc2 = 0;
      tk.forEach(function(w){ if (w.length > 2 && words.indexOf(w) >= 0) sc2 += w.length; });
      if (sc2 > bs) { bs = sc2; best = code; }
    });
    return best;
  }
  function teamAvgPts(code){
    var o = state.teamStats && state.teamStats.off; if (!o) return null;
    var c = o.cur && o.cur[code], q = o.prev && o.prev[code];
    if (c && q) { var w = c[0] / (c[0] + 6); return w * c[1] + (1 - w) * q[1]; }
    return c ? c[1] : q ? q[1] : null;
  }
  function lgAvgPts(){
    var o = state.teamStats && state.teamStats.off; if (!o) return 84;
    var ks = {}; Object.keys(o.prev || {}).forEach(function(k){ ks[k] = 1; }); Object.keys(o.cur || {}).forEach(function(k){ ks[k] = 1; });
    var v = Object.keys(ks).map(teamAvgPts).filter(function(x){ return x; });
    return v.length ? v.reduce(function(a, b){ return a + b; }, 0) / v.length : 84;
  }
  function linesFor(club, opp){
    var L = state.lines && state.lines.games; if (!L || !club || !opp) return null;
    // samo kvote za tačno ovu utakmicu i samo ako su sveže (stare kvote drugih utakmica bi pogrešno pomerale procenu)
    if (state.lines.at && Date.now() - Date.parse(state.lines.at) > 4 * 864e5) return null;
    var g = L[club + '-' + opp] || L[opp + '-' + club], home = !!L[club + '-' + opp];
    if (!g) return null;
    var tt = home ? g.hTot : g.aTot, ot = home ? g.aTot : g.hTot;
    if (tt == null && g.total != null && ot != null) tt = g.total - ot;
    return {teamTot: tt, oppTot: ot, total: g.total != null ? g.total : (tt != null && ot != null ? tt + ot : null)};
  }
  function pickCtx(pk){
    var C = ctx(); if (!C) return null;
    var club = C.el.tmap[pk.t], opp = club ? C.opp[club] : null, k = nkey(pk.p), ix = {P: 0, S: 1, A: 2}[pk.s], f = 1, ratio = null;
    if (opp && C.allowed[opp] && C.league[ix]) { ratio = C.allowed[opp][ix] / C.league[ix]; f = Math.max(0.85, Math.min(1.15, 1 + 0.6 * (ratio - 1))); }
    var oc = opp && C.el.clubs && C.el.clubs[opp];
    var gp = club && opp && C.pace[club] && C.pace[opp] && C.lgPace ? ((C.pace[club] + C.pace[opp]) / 2) / C.lgPace : null;
    var dr = opp && C.drtg[opp] && C.lgDrtg ? C.drtg[opp] / C.lgDrtg : null;
    var fx = pk.s === 'P' ? (dr ? Math.max(0.85, Math.min(1.15, 1 + 0.6 * (dr - 1))) : f) * (gp ? 1 + 0.6 * (gp - 1) : 1) : f * (gp ? 1 + 0.3 * (gp - 1) : 1);
    var LN = linesFor(club, opp), tAvg = club ? teamAvgPts(club) : null, lg = lgAvgPts(), cl = function(v, a, b){ return Math.max(a, Math.min(b, v)); };
    if (LN) {
      var fxL = null;
      if (LN.teamTot != null && tAvg) { var rr = LN.teamTot / tAvg; if (pk.s === 'P') fxL = cl(Math.pow(rr, 0.9), 0.82, 1.18); else if (pk.s === 'A') fxL = cl(Math.pow(rr, 0.7), 0.85, 1.15); }
      else if (LN.total != null && pk.s !== 'S') fxL = cl(Math.pow(LN.total / (2 * lg), 0.8), 0.85, 1.15);
      if (pk.s === 'S' && LN.total != null) fxL = cl(Math.pow(LN.total / (2 * lg), 0.5), 0.9, 1.1);
      if (fxL != null) fx = Math.pow(fx, 0.65) * Math.pow(fxL, 0.35);
    }
    return {club: club, opp: opp, oppName: oc ? (oc.abbr || oc.name) : '', ratio: ratio, f: f, fx: fx, gp: gp, dr: dr, ln: LN, tAvg: tAvg, b: C.boost[k] || 1, bp: C.boostPos[k] || 0, posWho: C.posWho[k] || [], pos: C.pos[k] || '', out: !!C.absent[k], absWho: club ? (C.absWho[club] || []) : []};
  }
  function normCdf(z){ var t = 1 / (1 + 0.2316419 * Math.abs(z)), d = 0.3989423 * Math.exp(-z * z / 2), q = d * t * (0.3193815 + t * (-0.3565638 + t * (1.781478 + t * (-1.821256 + t * 1.330274)))); return z > 0 ? 1 - q : q; }
  function poisCdf(k, m){ var sum = 0, term = Math.exp(-m); for (var i = 0; i <= k; i++) { if (i > 0) term *= m / i; sum += term; } return sum; }
  function modelUnder(stat, line, avg){
    if (avg == null) return null;
    if (stat === 'P') return normCdf((line - avg) / (0.35 * avg + 2.5));
    return poisCdf(Math.floor(line), Math.max(avg, 0.1));
  }
  var ML_IDX = null;
  function minLogOf(name){
    var M = state.minLog && state.minLog.m; if (!M) return null;
    if (!ML_IDX || ML_IDX.src !== M) ML_IDX = {src: M, keys: Object.keys(M)};
    return keyMatch(M, ML_IDX.keys, nkey(name));
  }
  function minStab(name){
    var a = minLogOf(name); if (!a) return null;
    var r = a.filter(function(m){ return m > 0.5; }).slice(-10), n = r.length;
    if (n < 3) return {n: n, cv: null};
    var mean = r.reduce(function(x, y){ return x + y; }, 0) / n, sd = Math.sqrt(r.reduce(function(x, y){ return x + (y - mean) * (y - mean); }, 0) / n);
    return {n: n, cv: mean > 0 ? sd / mean : null, mean: mean, lo: Math.min.apply(null, r), hi: Math.max.apply(null, r)};
  }
  // Procena iz 7 kola (848 minusa iz cele ponude): kvote su osnova, ali vrede samo upola; asistencije, skokovi i poeni od 10,5 prolaze češće;
  // igrači sa 21+ minuta češće od onih sa malo minuta; nestabilna minutaža (koeficijent varijacije iznad 0,3) najviše obara minus.
  var EST = {c: 0.16, kf: 0.5, A: 0.12, S: 0.08, P10: 0.12};
  // v6 (24.10.2026, 1.124 minusa iz cele ponude, 8 dana): kontekst utakmice. Protivnik koji dobro brani igračevu poziciju i spor meč (malo očekivanih poena tima)
  // podižu šansu; tesan meč (razlika do 5 poena) podiže; vruća forma (učinak po minutu u poslednje 3 iznad 130% sezone) i rezervista autsajdera obaraju.
  // Na najboljoj četvrtini ponude prolaz je porastao sa 62% na 69% i bio bolji u 6 od 8 dana. Koeficijenti su namerno umereni (mali uzorak).
  var ADJ = {of: 1.5, pace: 1.5, close: 0.2, hot: 0.15, dogB: 0.1, taA: 1.0};
  // 29.10.2026: za asistencije se dodatno računa koliko asistencija protivnik ukupno dozvoljava (na 241 minusu: najbolja trećina 66% → 68 do 70%); za skokove isti faktor u podacima ne radi, pa se ne koristi
  var C2_IDX = null;
  function ctx2Adj(pk, X){
    var C2 = state.ctx2; if (!C2 || !C2.pl) return null;
    if (!C2_IDX || C2_IDX.src !== C2.pl) C2_IDX = {src: C2.pl, keys: Object.keys(C2.pl)};
    var pl = keyMatch(C2.pl, C2_IDX.keys, nkey(pk.p)), ix = {P: 0, S: 1, A: 2}[pk.s], club = X && X.club, opp = X && X.opp, tm = C2.tm || {}, lgp = C2.lgp || 85, LN = X && X.ln;
    var r = {pos: pl ? pl[0] : '', of: null, pace: null, spread: null, close: false, hot: false, dogB: false, src: '', dz: 0};
    if (opp && r.pos && C2.of && C2.of[opp] && C2.of[opp][r.pos]) r.of = Math.max(0.8, Math.min(1.2, C2.of[opp][r.pos][ix]));
    if (LN && LN.teamTot != null) { r.pace = LN.teamTot / lgp; r.src = 'kvote'; }
    else if (club && opp && tm[club] && tm[opp]) { r.pace = ((tm[club][0] + tm[opp][1]) / 2) / lgp; r.src = 'proseci'; }
    if (r.pace != null) r.pace = Math.max(0.85, Math.min(1.15, r.pace));
    if (LN && LN.teamTot != null && LN.oppTot != null) r.spread = LN.teamTot - LN.oppTot;
    else if (club && opp && tm[club] && tm[opp]) r.spread = (tm[club][0] - tm[club][1]) - (tm[opp][0] - tm[opp][1]);
    if (r.spread != null) { r.close = Math.abs(r.spread) <= 5; r.dogB = r.spread < -5 && pl && pl[1] < 0.5; }
    r.hot = !!(pl && pl[5] >= 3 && pl[2 + ix] > 1.3);
    if (pk.s === 'A' && opp && C2.ta && C2.ta[opp]) r.taA = Math.max(0.75, Math.min(1.25, C2.ta[opp][2]));
    r.dz = (r.of != null ? -ADJ.of * (r.of - 1) : 0) + (r.pace != null ? -ADJ.pace * (r.pace - 1) : 0) + (r.close ? ADJ.close : 0) - (r.hot ? ADJ.hot : 0) - (r.dogB ? ADJ.dogB : 0) - (r.taA ? ADJ.taA * (r.taA - 1) : 0);
    return r;
  }
  function lgt(p){ p = Math.max(0.02, Math.min(0.98, p)); return Math.log(p / (1 - p)); }
  function roleOf(mp){ return mp == null ? '' : mp >= 25 ? 'start' : mp >= 21 ? 'rot' : mp >= 12 ? 'klupa' : 'dno'; }
  function estimate(pk, H){
    var fair = pk.o ? (1 / pk.u) / (1 / pk.u + 1 / pk.o) : (1 / pk.u) / 1.06;
    var A = avgFor(pk.p, pk.s), X = pickCtx(pk), mean = A && A.v != null ? A.v * (X ? (X.fx || X.f) * X.b : 1) : null, mp = mean != null ? modelUnder(pk.s, pk.l, mean) : null;
    var gp = H.ps[deacc(pk.p) + '|' + pk.s];
    var mpM = A && A.minP != null ? A.minP : null, ms = minStab(pk.p), b = X ? X.b : 1, z = EST.c + EST.kf * lgt(fair), why = [];
    if (pk.s === 'A') { z += EST.A; why.push('asistencije +'); }
    else if (pk.s === 'S') { z += EST.S; why.push('skokovi +'); }
    else if (pk.l >= 10.5) { z += EST.P10; why.push('poeni 10,5+ +'); }
    if (mpM != null) { var dz = mpM < 12 ? -0.25 : mpM < 17 ? -0.08 : mpM < 21 ? 0 : mpM < 25 ? 0.15 : 0.12; z += dz; }
    if (ms && ms.cv != null) { var pen = 0.4 * Math.max(0, Math.min(1, (ms.cv - 0.2) / 0.15)); z -= pen; }
    if (b > 1.02) z -= (mpM != null && mpM >= 25 ? 1.2 : 2.5) * (b - 1);
    var adj = ctx2Adj(pk, X); if (adj) z += adj.dz;
    // ritam i odbrana su sada u kontekstu, pa se za ovaj deo koristi prosek bez njih (da se ne računaju dvaput)
    var mpR = adj && A && A.v != null ? modelUnder(pk.s, pk.l, A.v * b) : mp;
    var nEff = !A || A.v == null ? 0 : (A.car && A.car.g ? Math.min(A.car.g - (A.cur ? A.cur.g : 0), 60) : 0) + (A.cur ? A.cur.g * 3 : 0);
    if (mpR != null && nEff > 0) z += 0.25 * nEff / (nEff + 20) * (lgt(mpR) - lgt(fair));
    var p = Math.max(0.3, Math.min(0.8, 1 / (1 + Math.exp(-z))));
    return {fair: fair, pr: p, ev: p * pk.u - 1, np: gp ? gp.n : 0, hp: gp ? gp.h : 0, avg: A, mp: mp, mean: mean, cx: X, out: X ? X.out : false, ms: ms, mpM: mpM, role: roleOf(mpM), adj: adj};
  }
  function level(sc){
    if (sc >= 0.03) return ['dobro', 'Vrlo dobar', 5];
    if (sc >= 0) return ['dobro', 'Dobar', 4];
    if (sc >= -0.04) return ['neutral', 'Prosečan', 3];
    if (sc >= -0.08) return ['lose', 'Slab', 2];
    return ['lose', 'Loš', 1];
  }
  function meter(sc){
    var L = level(sc), bars = '';
    for (var i = 1; i <= 5; i++) bars += '<i' + (i <= L[2] ? ' class="on"' : '') + '></i>';
    return '<span class="tag ' + L[0] + '" style="display:inline-flex;align-items:center;gap:6px"><span class="meter">' + bars + '</span>' + L[1] + '</span>';
  }
  function poolList(){
    var off = getOffer(), g = genCfg(), H = histMaps();
    if (!off || !off.picks) return [];
    var list = off.picks.filter(function(pk){ return g.stats[pk.s]; }).map(function(pk){
      var e = estimate(pk, H); return Object.assign({k: pk.c + pk.s}, pk, e);
    });
    var byS = g.focus !== 'vrednost';
    list.forEach(function(x){
      x.margin = x.mean != null ? x.l - x.mean : null; x.okAbove = x.margin != null && x.margin >= (x.s === 'P' ? 1 : 0.4);
      x.main = false; x.dMin = 0; x.dTeam = 0; x.prG = x.pr;
      var mpM = x.mpM, cv = x.ms ? x.ms.cv : null, b = x.cx ? x.cx.b : 1, bp = x.cx ? x.cx.bp || 0 : 0, st = mpM != null && mpM >= 25;
      x.unst = cv != null && cv > 0.3; x.weak = st ? b >= 1.15 || bp >= 0.10 : b >= 1.10 || bp >= 0.07; x.low = mpM != null && mpM < 12;
      x.inj = injuryOf(x.p);
      x.cls = x.unst || x.weak || x.low || (x.inj && (x.inj.s === 'out' || x.inj.s === 'doubtful')) ? 'C' : st || cv == null ? 'B' : 'A';
      x.capF = {A: 1, B: 0.6, C: 0.3}[x.cls];
    });
    list.sort(function(a, b){ return byS ? b.prG - a.prG : b.ev - a.ev; });
    var n = list.length;
    var mnO2 = num(g.minOdds), mxO2 = num(g.maxOdds);
    var elig = list.filter(function(x){ return !(mnO2 && x.u < mnO2) && !(mxO2 && x.u > mxO2) && !x.out && x.cls !== 'C'; });
    var topN = elig.length >= 5 ? Math.max(1, Math.round(elig.length * 0.2)) : 0, topSet = {};
    elig.slice(0, topN).forEach(function(x){ topSet[x.k] = 1; });
    list.forEach(function(x, i){ x.strong = !!topSet[x.k]; x.g = x.cx && x.cx.club && x.cx.opp ? [x.cx.club, x.cx.opp].sort().join('-') : ''; });
    var bestOf = {};
    list.forEach(function(x){ if (x.out || !g.stats[x.s] || (mnO2 && x.u < mnO2) || (mxO2 && x.u > mxO2) || g.excl[x.k]) return; var pk = deacc(x.p); if (!bestOf[pk] || x.pr > bestOf[pk].pr) bestOf[pk] = x; });
    list.forEach(function(x){ var bb = bestOf[deacc(x.p)]; x.alt = !!(bb && bb !== x); x.altOf = x.alt ? bb.s : ''; });
    return list;
  }
  function activePool(){
    var g = genCfg(), mn = num(g.minOdds), mx = num(g.maxOdds);
    return poolList().filter(function(x){
      if (x.out) return false;
      if (g.forced[x.k]) return true;
      if (g.excl[x.k]) return false;
      if (g.best && x.alt) return false;
      if (g.needAbove && !x.okAbove && !g.opt) return false;
      if (g.onlyPos && x.ev <= 0 && !g.opt) return false;
      if (mn && x.u < mn) return false;
      if (mx && x.u > mx) return false;
      return true;
    });
  }
  function rotW(x){
    var g = genCfg(); if (!g.rot) return 1;
    var w = x.cls === 'A' ? 1.4 : x.cls === 'C' ? 0.5 : 1;
    var tt = x.cx && x.cx.ln && x.cx.ln.teamTot;
    if (tt != null) w *= Math.max(0.85, Math.min(1.2, Math.exp(-(tt - 84) / 25)));
    return w;
  }
  function rng32(seed){ var a = seed >>> 0; return function(){ a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function optimizeTickets(tickets, cands, o){
    var M = 4096, W = M / 32, R = rng32(Date.now() % 1e9), BETA = o.beta == null ? 1 : o.beta;
    var plCapOf = o.plCapOf || function(){ return o.plCap; };
    var pOf = function(x){ return Math.max(0.01, x.prG != null ? x.prG : x.pr); };
    var K = {}; cands.forEach(function(x, i){ K[x.k] = i; });
    var bits = cands.map(function(x){ var a = new Uint32Array(W), p = x.prG != null ? x.prG : x.pr; for (var w = 0; w < W; w++) { var v = 0; for (var b = 0; b < 32; b++) if (R() < p) v |= (1 << b); a[w] = v >>> 0; } return a; });
    var pkey = function(x){ return deacc(x.p); }, tkey = function(x){ return deacc(x.t); };
    var T = tickets.map(function(t){ var c = t.slice(); c.allow = t.allow; c.stack = t.stack; return c; });
    var uses = {}, usesP = {};
    T.forEach(function(t){ t.forEach(function(x){ uses[x.k] = (uses[x.k] || 0) + 1; usesP[pkey(x)] = (usesP[pkey(x)] || 0) + 1; }); });
    var fixedN = o.forcedN || 0;
    var okSwap = function(t, j, q){
      var old = t[j];
      if (q.k === old.k) return false;
      if (t.allow && q.g && !t.allow[q.g]) return false;
      for (var i = 0; i < t.length; i++) if (i !== j && pkey(t[i]) === pkey(q)) return false;
      if ((uses[q.k] || 0) >= o.capPair(q)) return false;
      if (pkey(q) !== pkey(old) && (usesP[pkey(q)] || 0) >= plCapOf(q)) return false;
      var tc = 0; for (var i2 = 0; i2 < t.length; i2++) if (i2 !== j && tkey(t[i2]) === tkey(q)) tc++;
      if (tc >= o.maxTeam) return false;
      return true;
    };
    var doSwap = function(t, j, q){ var old = t[j]; uses[old.k]--; usesP[pkey(old)]--; uses[q.k] = (uses[q.k] || 0) + 1; usesP[pkey(q)] = (usesP[pkey(q)] || 0) + 1; t[j] = q; };
    // 1) coverage: every player in the pool on at least minCov tickets
    if (o.minCov > 0) {
      var byP = {}; cands.forEach(function(x){ if (o.covOk && !o.covOk(x)) return; (byP[pkey(x)] = byP[pkey(x)] || []).push(x); });
      Object.keys(byP).forEach(function(pk){
        var opts = byP[pk].slice().sort(function(a, b){ return b.pr - a.pr; });
        var guard = 0;
        while ((usesP[pk] || 0) < o.minCov && guard++ < 200) {
          var q = opts[Math.floor(R() * Math.min(2, opts.length))], ti = Math.floor(R() * T.length), t = T[ti];
          var j = fixedN + Math.floor(R() * (t.length - fixedN)), old = t[j];
          if ((usesP[pkey(old)] || 0) <= o.minCov && (!o.covOk || o.covOk(old))) continue;
          if (okSwap(t, j, q)) doSwap(t, j, q);
        }
      });
    }
    // 2) local search: najveći očekivani broj dobitnih tiketa (tačno, iz šansi), uz dodatak za scenarije u kojima prolazi bar jedan tiket
    var prodOf = function(t){ return t.reduce(function(a, x){ return a * pOf(x); }, 1); }, prod = T.map(prodOf);
    var hitOf = function(t){ var h = new Uint32Array(W); h.fill(0xFFFFFFFF); t.forEach(function(x){ var bx = bits[K[x.k]]; if (!bx) return; for (var w = 0; w < W; w++) h[w] &= bx[w]; }); return h; };
    var H = T.map(hitOf), cnt = new Uint16Array(M), covered = 0;
    H.forEach(function(h){ for (var w = 0; w < W; w++) { var v = h[w]; while (v) { var b = 31 - Math.clz32(v); v &= ~(1 << b); var sIdx = w * 32 + b; if (cnt[sIdx]++ === 0) covered++; } } });
    var nh = new Uint32Array(W);
    for (var it = 0; it < (o.iters || 30000); it++) {
      var ti2 = Math.floor(R() * T.length), t2 = T[ti2]; if (t2.length <= fixedN) continue;
      var j2 = fixedN + Math.floor(R() * (t2.length - fixedN)), old2 = t2[j2];
      if (o.minCov > 0 && (usesP[pkey(old2)] || 0) <= o.minCov && (!o.covOk || o.covOk(old2))) continue;
      var q2 = cands[Math.floor(R() * cands.length)];
      if (!okSwap(t2, j2, q2)) continue;
      nh.fill(0xFFFFFFFF);
      for (var i3 = 0; i3 < t2.length; i3++) { var bx2 = bits[K[(i3 === j2 ? q2 : t2[i3]).k]]; if (!bx2) continue; for (var w2 = 0; w2 < W; w2++) nh[w2] &= bx2[w2]; }
      var oh = H[ti2], delta = 0;
      for (var w3 = 0; w3 < W; w3++) {
        var d = (oh[w3] ^ nh[w3]) >>> 0; if (!d) continue;
        while (d) { var b3 = 31 - Math.clz32(d); d &= ~(1 << b3); var s3 = w3 * 32 + b3; if (oh[w3] & (1 << b3)) { if (cnt[s3] === 1) delta--; } else { if (cnt[s3] === 0) delta++; } }
      }
      var dW = prod[ti2] * (pOf(q2) / pOf(old2) - 1);
      if (M * dW + BETA * delta >= 0) {
        for (var w4 = 0; w4 < W; w4++) {
          var d4 = (oh[w4] ^ nh[w4]) >>> 0;
          while (d4) { var b4 = 31 - Math.clz32(d4); d4 &= ~(1 << b4); var s4 = w4 * 32 + b4; if (oh[w4] & (1 << b4)) { if (--cnt[s4] === 0) covered--; } else { if (cnt[s4]++ === 0) covered++; } }
        }
        H[ti2] = nh.slice(); doSwap(t2, j2, q2); prod[ti2] = prodOf(t2);
      }
    }
    T.optScore = covered / M;
    T.expWins = prod.reduce(function(a, b){ return a + b; }, 0);
    return T;
  }
  function generatePlan(){
    var g = genCfg(), total = num(g.total), sizes = [];
    for (var mi = 0; mi < g.mix.length; mi++) {
      if (!String(g.mix[mi].legs).trim() && !String(g.mix[mi].n).trim()) continue;
      var ml = parseInt(g.mix[mi].legs, 10), mn = parseInt(g.mix[mi].n, 10);
      if (!(ml >= 1 && ml <= 20)) return 'Red ' + (mi + 1) + ': broj parova treba da bude od 1 do 20.';
      if (!(mn >= 1)) return 'Red ' + (mi + 1) + ': upiši broj tiketa.';
      for (var z = 0; z < mn; z++) sizes.push(ml);
    }
    var N = sizes.length;
    if (!N) return 'Dodaj bar jedan red sa brojem parova i tiketa.';
    if (N > 100) return 'Najviše 100 tiketa odjednom.';
    if (!(total > 0)) return 'Upiši ukupan ulog.';
    var plShare = num(g.maxPl), plCap = plShare > 0 ? Math.max(1, Math.floor(N * plShare / 100)) : N;
    var maxUse = parseInt(g.maxUse, 10); if (!(maxUse >= 1)) maxUse = plCap;
    var maxTeam = parseInt(g.maxTeam, 10); if (!(maxTeam >= 1)) maxTeam = 99;
    sizes.sort(function(a, b){ return b - a; });

    var pool = activePool();
    var forced = pool.filter(function(x){ return g.forced[x.k]; }), free = pool.filter(function(x){ return !g.forced[x.k]; });
    var fp = {}; forced.forEach(function(x){ fp[deacc(x.p)] = (fp[deacc(x.p)] || 0) + 1; });
    if (Object.keys(fp).some(function(k){ return fp[k] > 1; })) return 'Isti igrač je dva puta označen kao obavezan. Ostavi samo jedan njegov par.';
    if (forced.length >= sizes[sizes.length - 1] && sizes.some(function(n){ return n <= forced.length; })) return 'Obaveznih izbora (' + forced.length + ') ima koliko i parova na najkraćem tiketu ili više. Smanji broj obaveznih.';
    var slots = sizes.reduce(function(a, n){ return a + n - forced.length; }, 0);
    var playersFree = {}; free.forEach(function(x){ playersFree[deacc(x.p)] = 1; });
    var need = sizes[0] - forced.length;
    if (Object.keys(playersFree).length < need) return 'Za najduži tiket treba još ' + need + ' različitih igrača, a u izboru ih je ' + Object.keys(playersFree).length + '. Uključi više izbora.';

    var teamsAll = {}; pool.forEach(function(x){ teamsAll[deacc(x.t)] = 1; });
    var nTeams = Object.keys(teamsAll).length;
    if (maxTeam < 99 && nTeams * maxTeam < sizes[0]) return 'U izboru su igrači iz ' + nTeams + ' timova, pa sa najviše ' + maxTeam + ' igrača iz istog tima tiket može imati najviše ' + (nTeams * maxTeam) + ' parova. Povećaj „Najviše igrača iz istog tima“ ili smanji broj parova.';
    var base = Math.max(1, Math.ceil(slots / Math.max(1, free.length)));
    var capFor = function(x, b){ return g.balance ? (g.strong && x.strong ? maxUse : Math.min(maxUse, b)) : maxUse; };
    var capSum = function(b){ return free.reduce(function(a, x){ return a + capFor(x, b); }, 0); };
    var warn = '';
    while (capSum(base) < slots && base < maxUse) base++;
    if (capSum(base) < slots) return 'Premalo parova za ovoliko tiketa: treba popuniti ' + slots + ' mesta, a sa najviše ' + maxUse + ' tiketa po paru staje ' + capSum(base) + '. Povećaj „Najviše tiketa po paru“, uključi više izbora' + (g.best ? ', isključi „samo najjača stavka po igraču“' : '') + ' ili smanji broj tiketa.';

    var stackN = Math.min(N, Math.max(0, parseInt(g.stackN, 10) || 0)), stackK = Math.max(2, parseInt(g.stackK, 10) || 4), gameOrder = [], gameLbl = {};
    if (stackN) {
      var gs = {};
      free.forEach(function(x){ if (!x.g) return; var o = gs[x.g] || (gs[x.g] = {n: 0, ev: 0, players: {}}); o.n++; o.ev += g.focus !== 'vrednost' ? x.pr : x.ev; o.players[deacc(x.p)] = 1; });
      gameOrder = Object.keys(gs).filter(function(k){ return Object.keys(gs[k].players).length >= stackK; }).sort(function(a, b){ return gs[b].ev / gs[b].n - gs[a].ev / gs[a].n; });
      if (!gameOrder.length) return 'Za tikete oko jedne utakmice treba ponuda sa statistikom i bar ' + stackK + ' igrača iz iste utakmice. Preuzmi ponudu novim pomoćnikom ili smanji broj parova iz iste utakmice.';
      var C0 = ctx(); gameOrder.forEach(function(k){ var q = k.split('-'); gameLbl[k] = q.map(function(c){ var cl = C0 && C0.el.clubs[c]; return cl ? (cl.abbr || cl.name) : c; }).join(' – '); });
    }
    // ponavljanje po grupi: A (stabilna minutaža, do 25 min) do pune granice, B (starteri, nepoznata minutaža) 60%, C (nestabilni, ispod 12 min, oslabljena pozicija) 30%
    var relax = 0, RL = [0, 0.25, 0.5, 0.75, 1];
    var clsF = function(x){ if (!g.rot) return 1; var f = x.capF || 1; return f + relax * (1 - f); };
    var pairCap = function(x){ return Math.max(1, Math.round((g.opt ? maxUse : capFor(x, base)) * clsF(x))); };
    var plCapOf = function(x){ return Math.max(1, Math.round(plCap * clsF(x))); };
    var roomOf = function(){ var byP = {}; free.forEach(function(x){ var k = deacc(x.p), o = byP[k] || (byP[k] = {pc: 0, pl: 0}); o.pc += pairCap(x); o.pl = Math.max(o.pl, plCapOf(x)); }); return Object.keys(byP).reduce(function(a, k){ return a + Math.min(byP[k].pc, byP[k].pl); }, 0); };
    for (var ri = 0; ri < RL.length; ri++) { relax = RL[ri]; if (roomOf() >= Math.ceil(slots * 1.1)) break; }
    var plRoom = roomOf();
    if (plRoom < slots) return 'Uz pravilo da jedan igrač bude najviše na ' + plCap + ' od ' + N + ' tiketa (' + Math.round(plShare) + '%)' + (maxUse < plCap ? ' i par najviše na ' + maxUse : '') + ', ima mesta za ' + plRoom + ' od potrebnih ' + slots + ' parova. Smanji broj tiketa ili parova, uključi više igrača' + (g.best ? ', isključi „samo najjača stavka po igraču“' : '') + ' ili povećaj „Najviše tiketa po igraču ukupno“.';
    var stackIdx = {}; for (var si = 0; si < stackN; si++) stackIdx[Math.round(si * N / stackN)] = gameOrder[si % gameOrder.length];
    var gamesAll = {}; free.forEach(function(x){ if (x.g) gamesAll[x.g] = 1; });
    var GL = Object.keys(gamesAll), gShare = num(g.gameShare), allowSets = null;
    if (GL.length >= 2 && gShare > 0 && gShare < 100) {
      var kG = Math.max(1, Math.floor(GL.length * gShare / 100)), maxLegs = Math.max.apply(null, sizes);
      while (kG < GL.length && kG * 2 * maxTeam < maxLegs) kG++;
      if (kG < GL.length) {
        var combos = [];
        (function rec(st, cur){ if (combos.length > 400) return; if (cur.length === kG) { combos.push(cur.slice()); return; } for (var i = st; i < GL.length; i++) { cur.push(GL[i]); rec(i + 1, cur); cur.pop(); } })(0, []);
        var gc = {}; GL.forEach(function(x){ gc[x] = 0; });
        allowSets = [];
        for (var ti0 = 0; ti0 < N; ti0++) {
          var bestC = null, bs = Infinity;
          combos.forEach(function(c){ var sc0 = c.reduce(function(a, x){ return a + gc[x]; }, 0) + Math.random() * 0.5; if (sc0 < bs) { bs = sc0; bestC = c; } });
          var o0 = {}; bestC.forEach(function(x){ gc[x]++; o0[x] = 1; }); allowSets.push(o0);
        }
      }
    }
    function attemptPlan(){
      var uses = {}, usesP = {}, tickets = [], seen = {};
      for (var t = 0; t < N; t++) {
        var L = sizes[t] - forced.length, best = null, sg = stackIdx[t];
        for (var attempt = 0; attempt < 40 && !best; attempt++) {
          var legs = [], usedP = {}, teamCnt = {}, ok = true;
          forced.forEach(function(x){ usedP[deacc(x.p)] = 1; var tk = deacc(x.t); teamCnt[tk] = (teamCnt[tk] || 0) + 1; });
          for (var j = 0; j < L; j++) {
            var inStack = sg && j < Math.min(stackK, L);
            var cand = free.filter(function(x){ var pk3 = deacc(x.p); return (uses[x.k] || 0) < pairCap(x) && (usesP[pk3] || 0) < plCapOf(x) && !usedP[pk3] && (!allowSets || !x.g || allowSets[t][x.g]) && (inStack ? x.g === sg : (teamCnt[deacc(x.t)] || 0) < maxTeam); });
            if (!cand.length && inStack) cand = free.filter(function(x){ return !usedP[deacc(x.p)] && x.g === sg; });
            if (!cand.length) { ok = false; break; }
            var minU = Math.min.apply(null, cand.map(function(x){ return uses[x.k] || 0; }));
            var ws = cand.map(function(x){ var u = uses[x.k] || 0; return (g.focus !== 'vrednost' ? Math.exp(14 * ((x.prG != null ? x.prG : x.pr) - 0.55)) : Math.exp(6 * x.ev)) * (g.balance ? Math.pow(0.15, u - minU) : 1 / (1 + u)) * rotW(x) * (g.pref[x.k] || 1); });
            var sum = ws.reduce(function(a, b){ return a + b; }, 0), r = Math.random() * sum, pick = cand[cand.length - 1];
            for (var q = 0; q < cand.length; q++) { r -= ws[q]; if (r <= 0) { pick = cand[q]; break; } }
            legs.push(pick); usedP[deacc(pick.p)] = 1; teamCnt[deacc(pick.t)] = (teamCnt[deacc(pick.t)] || 0) + 1;
          }
          if (!ok) continue;
          var sig = legs.map(function(x){ return x.k; }).sort().join(',');
          if (seen[sig] && attempt < 39) continue;
          seen[sig] = 1; best = legs;
        }
        if (!best) return null;
        best.forEach(function(x){ uses[x.k] = (uses[x.k] || 0) + 1; var pk2 = deacc(x.p); usesP[pk2] = (usesP[pk2] || 0) + 1; });
        var tl = forced.concat(best); if (sg) { tl.stack = sg; } if (allowSets) tl.allow = allowSets[t];
        tickets.push(tl);
      }
      return tickets;
    }
    var tickets = null;
    for (var tries = 0; tries < 25 && !tickets; tries++) { tickets = attemptPlan(); if (!tickets && tries % 5 === 4 && relax < 1) relax = Math.min(1, relax + 0.25); }
    if (g.rot && relax > 0) warn = 'Za ovoliko tiketa nije bilo dovoljno stabilnih rezervista, pa su starteri i igrači sa nestabilnom minutažom pušteni na više tiketa nego inače (ograničenje olabavljeno ' + Math.round(relax * 100) + '%).';
    if (!tickets) return 'Nije moguće složiti tikete sa ovim ograničenjima. Olabavi ih: povećaj broj tiketa po paru ili igrača iz istog tima' + (allowSets ? ', povećaj „Svaka utakmica najviše na % tiketa“' : '') + ' ili uključi više izbora.';
    if (g.opt) {
      var minCov = Math.max(0, parseInt(g.minCov, 10) || 0);
      var prs = free.map(function(x){ return x.pr; }).sort(function(a, b){ return a - b; }), covMin = prs.length ? prs[Math.floor(prs.length * 0.4)] : 0;
      tickets = optimizeTickets(tickets, free, {capPair: pairCap, plCapOf: plCapOf, maxTeam: maxTeam, minCov: minCov, covOk: function(x){ return x.cls !== 'C' && x.pr >= covMin; }, forcedN: forced.length, iters: 40000});
    }
    tickets.sort(function(a, b){ return a.length - b.length; });
    var stake = Math.floor(total / N);
    var optScore = tickets.optScore, expWins = tickets.expWins;
    ui.plan = {at: new Date().toISOString(), round: String(g.round || '').trim(), warn: warn, sim: null, opt: optScore, expWins: expWins, tickets: tickets.map(function(legs){
      return {stake: stake, stack: legs.stack || '', stackLbl: legs.stack ? gameLbl[legs.stack] : '', legs: legs.map(function(x){ return {c: x.c, p: x.p, t: x.t, s: x.s, l: x.l, u: x.u, pr: Math.round(x.pr * 1000) / 1000, fa: Math.round(x.fair * 1000) / 1000, sc: Math.round(x.ev * 1000) / 1000, g: x.g || '', st: !!x.strong, f: !!g.forced[x.k]}; })};
    })};
    return '';
  }
  function invNorm(p){
    var a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239],
        b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572],
        c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783],
        d = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416], q, r;
    if (p < 0.02425) { q = Math.sqrt(-2 * Math.log(p)); return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    if (p > 1 - 0.02425) { q = Math.sqrt(-2 * Math.log(1 - p)); return -(((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((d[0] * q + d[1]) * q + d[2]) * q + d[3]) * q + 1); }
    q = p - 0.5; r = q * q; return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1);
  }
  function randn(){ var u = 0, v = 0; while (!u) u = Math.random(); while (!v) v = Math.random(); return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v); }
  function avgRefundPer100(){
    var sum = 0, n = 0;
    state.tickets.forEach(function(t){ if (t.refund) { sum += t.refund / t.stake * 100; n++; } });
    return n ? sum / n : 0;
  }
  function simulatePlan(plan, probOf, iters, rhoIn){
    var refundPer100 = avgRefundPer100();
    var idx = {}, pk = [], games = {}, gl = 0;
    plan.tickets.forEach(function(t){ t.legs.forEach(function(l){ var k = l.c + l.s; if (!(k in idx)) { idx[k] = pk.length; var pp = Math.min(0.995, Math.max(0.005, probOf(l))); if (l.g && !(l.g in games)) games[l.g] = gl++; pk.push({th: invNorm(pp), gi: l.g ? games[l.g] : -1}); } }); });
    var T = plan.tickets.map(function(t){ return {legs: t.legs.map(function(l){ return idx[l.c + l.s]; }), pay: t.stake * t.legs.reduce(function(a, l){ return a * l.u; }, 1) * (1 + admBonusPct(t.legs.length)), stake: t.stake}; });
    var total = T.reduce(function(a, t){ return a + t.stake; }, 0), rho = rhoIn == null ? 0 : rhoIn, sr = Math.sqrt(rho), se = Math.sqrt(1 - rho);
    var hits = new Uint8Array(pk.length), z = new Float64Array(Math.max(1, gl)), any = 0, sum = 0, prof = 0, w = [0, 0, 0, 0];
    for (var it = 0; it < iters; it++) {
      for (var g = 0; g < gl; g++) z[g] = randn();
      for (var i = 0; i < pk.length; i++) { var x = pk[i].gi >= 0 ? sr * z[pk[i].gi] + se * randn() : randn(); hits[i] = x < pk[i].th ? 1 : 0; }
      var wn = 0, ret = 0;
      for (var j = 0; j < T.length; j++) { var ms = 0, L = T[j].legs; for (var q = 0; q < L.length; q++) { if (!hits[L[q]]) { ms++; if (ms > 1) break; } } if (!ms) { wn++; ret += T[j].pay; } else if (ms === 1 && refundPer100) ret += refundPer100 * T[j].stake / 100; }
      if (wn) any++; w[Math.min(wn, 3)]++; sum += ret; if (ret > total) prof++;
    }
    return {any: any / iters, mean: sum / iters, total: total, w: w.map(function(x){ return x / iters; }), prof: prof / iters};
  }
  function runSim(){
    var p = ui.plan; if (!p) return;
    var sp = settledPicks(true), hr = sp.length ? sp.filter(function(e){ return e.status === 'hit'; }).length / sp.length : 0.53;
    var iters = 20000;
    p.sim = {at: Date.now(), hr: hr, rows: [
      ['Procena aplikacije', simulatePlan(p, function(l){ return l.pr || 0.5; }, iters)],
      ['Šanse po kladionici', simulatePlan(p, function(l){ return l.fa || (1 / l.u) / 1.04; }, iters)],
      ['Tvoj dosadašnji procenat (' + pct(hr) + ', ' + (rounds().length === 1 ? '1 kolo' : rounds().length + ' kola') + ')', simulatePlan(p, function(){ return hr; }, iters)]
    ]};
  }
  function simHtml(){
    var p = ui.plan; if (!p) return '';
    if (!p.sim) return '<div class="btns"><button class="btn" data-act="runSim">Pokreni simulaciju</button><span class="hint" style="margin:0;align-self:center">20.000 zamišljenih kola sa ovim tiketima.</span></div>';
    var rows = p.sim.rows.map(function(r){ var x = r[1]; return [esc(r[0]), pct(x.any), pct(x.w[0]), pct(x.prof), fmt(x.mean) + ' <small style="color:var(--muted)">(' + pct(x.mean / x.total) + ')</small>']; });
    return '<div style="margin-top:12px"><h3 style="margin:0 0 6px;font-size:16px">Simulacija</h3><p class="hint">Ovi tiketi su odigrani u 20.000 zamišljenih kola, uz tri pretpostavke o tome koliko često minusi prolaze. Uračunato je da se isti izbori ponavljaju na više tiketa, pa jedan promašaj obara sve tikete na kojima je taj izbor. Parovi se inače računaju kao nezavisni. Uračunat je i povraćaj kad tiket padne zbog samo jednog para, prema proseku tvojih dosadašnjih povraćaja, kao i bonus AdmiralBeta za broj parova (4 para 3%, 7 parova 11%, 8 parova 16%, 9 parova 21%, 10 parova 26%). Ako minusi iz iste utakmice stvarno češće prolaze zajedno, tiketi oko jedne utakmice imaju nešto veće šanse od prikazanih, a to se proverava kroz kola.</p>' +
      '<div class="scroll"><table class="sortable" data-sid="gen-sim">' + sortHead(['Pretpostavka', 'Bar jedan dobitni tiket', 'Nijedan dobitni tiket', 'Vratiš više nego uložiš', 'Prosečno vraćeno']) + '<tbody>' + rows.map(function(r){ return '<tr>' + r.map(function(c, k){ return '<td' + (k ? ' class="r"' : '') + '>' + c + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>' +
      '<p class="hint" style="margin-top:8px">Kako da čitaš: „bar jedan dobitni tiket“ je šansa da u kolu prođe makar jedan tiket. „Prosečno vraćeno“ je prosek preko mnogo kola; ako je manji od uloga, plan dugoročno gubi pod tom pretpostavkom. Red „Šanse po kladionici“ je najoprezniji i najrealniji dok ne skupiš više kola. Tvoj dosadašnji procenat je iz malog uzorka, pa taj red uzmi kao najbolji mogući slučaj. Probaj drugačiji broj tiketa, parova ili ulog, generiši ponovo i uporedi.</p>' +
      '<div class="btns" style="margin-top:0"><button class="btn sm" data-act="runSim">Ponovi simulaciju</button></div></div>';
  }
  function planJson(){
    var p = ui.plan; if (!p) return '';
    return JSON.stringify({v: 1, round: p.round, tickets: p.tickets.map(function(t){ return {stake: t.stake, legs: t.legs.map(function(l){ return {c: l.c, p: l.p, t: l.t || '', s: l.s, l: l.l, u: l.u}; })}; })});
  }
  function budgetHtml(planTotal){
    var b = state.settings && state.settings.budget, g = genCfg(), r = String(g.round || '').trim();
    if (!b) return '';
    var spent = r ? state.tickets.filter(function(t){ return String(t.round) === r; }).reduce(function(a, t){ return a + t.stake; }, 0) : 0;
    var after = spent + planTotal, over = after > b;
    return '<p class="hint" style="' + (over ? 'color:var(--miss);font-weight:600' : '') + '">Budžet po kolu: ' + fmt(b, 0) + ' din. ' + (r ? 'U kolu ' + esc(r) + ' je već uloženo ' + fmt(spent) + ' din, a sa ovim planom bilo bi ' + fmt(after) + ' din.' : 'Upiši kolo u podešavanjima da bi se računalo koliko je već uloženo.') + (over ? ' Ovo prelazi budžet.' : '') + '</p>';
  }
  function exposureRows(ticketLegs){
    var pl = {}, order = [];
    ticketLegs.forEach(function(legs){
      var seenP = {};
      legs.forEach(function(l){
        var k = deacc(l.p); if (!pl[k]) { pl[k] = {p: l.p, t: l.t, n: 0, picks: {}, st: false}; order.push(k); }
        if (!seenP[k]) { pl[k].n++; seenP[k] = 1; }
        var pk2 = l.s + '|' + l.l; pl[k].picks[pk2] = (pl[k].picks[pk2] || 0) + 1; if (l.st) pl[k].st = true;
      });
    });
    return order.sort(function(a, b){ return pl[b].n - pl[a].n; }).map(function(k){
      var x = pl[k];
      var parts = Object.keys(x.picks).sort(function(a, b){ return x.picks[b] - x.picks[a]; }).map(function(pk2){ var q = pk2.split('|'); return STAT[q[0]].toLowerCase() + ' ' + fmt(+q[1], 1) + ': ' + x.picks[pk2]; });
      return [(x.st ? '★ ' : '') + esc(x.p) + ' <small style="color:var(--muted)">' + esc(x.t || '') + '</small>', '' + x.n, parts.join(', ')];
    });
  }
  function playedRoundHtml(){
    var rs = rounds(); if (!rs.length) return '';
    var g = genCfg(), r = String(g.round || '').trim();
    if (rs.indexOf(r) < 0) r = rs[rs.length - 1];
    var list = state.tickets.filter(function(t){ return String(t.round) === r; });
    if (!list.length) return '';
    var stake = list.reduce(function(a, t){ return a + t.stake; }, 0);
    var rows = exposureRows(list.map(function(t){ return t.legs.map(function(l){ return {p: l.p, t: l.team, s: l.stat, l: l.line}; }); }));
    return '<section class="panel"><h2>Odigrano u kolu ' + esc(r) + '</h2><p class="hint">Stvarno upisani tiketi iz ovog kola: ' + list.length + ' tiketa, ukupno ' + fmt(stake) + ' din. Tabela pokazuje na koliko tiketa je svaki igrač, ukupno i po paru.</p>' +
      simpleTable('', '', ['Igrač','Tiketa ukupno','Parovi (tiketa)'], rows.slice(0, 200)).replace('<section class="panel"><h2></h2>', '').replace(/<\/section>$/, '') + '</section>';
  }
  function injuryHtml(off){
    var I = state.injuries;
    if (!I || !I.list || !I.list.length) return '<section class="panel"><h2>Izveštaj o povredama</h2><p class="hint">Za ovo kolo još nije unet. Pošalji Claude-u link ka izveštaju o povredama za kolo i on će ga uneti.</p></section>';
    var teams = {}; (off && off.picks || []).forEach(function(x){ teams[x.t] = 1; });
    var tn = Object.keys(teams), match = function(team){ if (!tn.length) return true; var w = deacc(team).split(/[^a-z]+/).filter(function(x){ return x.length > 2; }); return tn.some(function(t){ var tw = deacc(t).split(/[^a-z]+/); return w.some(function(x){ return tw.indexOf(x) >= 0; }); }); };
    var rows = I.list.filter(function(r){ return match(r.t); }).sort(function(a, b){ return a.t.localeCompare(b.t) || ({out: 0, doubtful: 1, dtd: 2})[a.s] - ({out: 0, doubtful: 1, dtd: 2})[b.s]; })
      .map(function(r){ return [esc(r.p), esc(r.t), '<span class="tag ' + (r.s === 'out' ? 'lose' : 'neutral') + '">' + INJ_TXT[r.s] + '</span>', esc(r.note || '')]; });
    return '<section class="panel"><h2>Izveštaj o povredama</h2><p class="hint">Kolo ' + esc(I.round || '') + ', stanje od ' + esc(I.at || '') + '. Izvor: ' + esc(I.src || '') + '. Igrači koji ne igraju izbacuju se iz izbora, a njihovi minuti raspoređuju saigračima (kad je ponuda preuzeta sa statistikom). Upitne igrače i one sa odlukom pred utakmicu možeš označiti u delu „Protivnici i odsustva“.</p>' +
      (rows.length ? '<div class="scroll"><table class="sortable" data-sid="gen-inj">' + sortHead(['Igrač', 'Tim', 'Status', 'Napomena'], 9) + '<tbody>' + rows.map(function(r){ return '<tr>' + r.map(function(c){ return '<td>' + c + '</td>'; }).join('') + '</tr>'; }).join('') + '</tbody></table></div>' : '<p class="hint">Nema prijavljenih povreda za timove iz ove ponude.</p>') + '</section>';
  }
  function dayOfIso(iso){ var d = new Date(iso); if (isNaN(d)) return String(iso || '').slice(0, 10); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  function timeOfIso(iso){ var d = new Date(iso); return isNaN(d) ? '' : String(d.getHours()).padStart(2, '0') + ':' + String(d.getMinutes()).padStart(2, '0'); }
  function snapPicks(od){ return (od.picks || []).map(function(p){ return [p.c, p.s, p.l, p.u, p.o == null ? null : p.o, p.p, p.t]; }); }
  function addSnap(list, od){
    var L = list.filter(function(x){ return x.at !== od.at; });
    L.push({at: od.at, picks: snapPicks(od)});
    L.sort(function(a, b){ return String(a.at).localeCompare(String(b.at)); });
    var cut = new Date(Date.now() - 21 * 864e5).toISOString();
    L = L.filter(function(x){ return String(x.at) >= cut; });
    var byDay = {}; L.forEach(function(x){ (byDay[dayOfIso(x.at)] = byDay[dayOfIso(x.at)] || []).push(x); });
    var out = [];
    Object.keys(byDay).sort().forEach(function(d){ var a = byDay[d]; if (a.length > 6) a = [a[0]].concat(a.slice(a.length - 5)); out = out.concat(a); });
    return out;
  }
  function snapsOfDay(list, day){ return (list || []).filter(function(x){ return dayOfIso(x.at) === day; }).sort(function(a, b){ return String(a.at).localeCompare(String(b.at)); }); }
  function offerDiff(basePicks, curPicks){
    var B = {}; basePicks.forEach(function(x){ B[x[0] + '|' + x[1]] = x; });
    var C = {}; curPicks.forEach(function(x){ C[x[0] + '|' + x[1]] = x; });
    var r = {up: [], down: [], oddsUp: [], oddsDown: [], added: [], removed: []};
    Object.keys(C).forEach(function(k){
      var c = C[k], b = B[k];
      if (!b) { r.added.push(c); return; }
      if (c[2] > b[2]) r.up.push([b, c]);
      else if (c[2] < b[2]) r.down.push([b, c]);
      else if (c[3] - b[3] >= 0.05) r.oddsUp.push([b, c]);
      else if (b[3] - c[3] >= 0.05) r.oddsDown.push([b, c]);
    });
    Object.keys(B).forEach(function(k){ if (!C[k]) r.removed.push(B[k]); });
    return r;
  }
  function offerMovesHtml(){
    var off = getOffer(); if (!off || !off.picks) return '';
    var snaps = state.offerSnaps || [], day = dayOfIso(off.at), todays = snapsOfDay(snaps, day);
    var h = '<section class="panel"><h2>Promene u ponudi</h2>';
    var cur = snapPicks(off), first = todays[0];
    if (!first || first.at === off.at) {
      h += '<p class="hint">Za ' + esc(day) + ' je sačuvano samo jedno stanje ponude (' + esc(timeOfIso(off.at)) + '). Učitaj ponudu ponovo kasnije, na primer oko podneva i 2 do 3 sata pre utakmica, pa ćeš ovde videti šta se promenilo.</p>';
    } else {
      var d = offerDiff(first.picks, cur);
      var row = function(pair, kind){ var b = pair[0], c = pair[1]; return [esc(c[5]) + ' <small style="color:var(--muted)">' + esc(c[6] || '') + '</small>', STAT[c[1]], kind === 'line' ? fmt(b[2], 1) + ' → ' + fmt(c[2], 1) : fmt(c[2], 1), fmt(b[3]) + ' → ' + fmt(c[3])]; };
      h += '<p class="hint">Poređenje prvog stanja danas (' + esc(timeOfIso(first.at)) + ') sa trenutnim (' + esc(timeOfIso(off.at)) + '). Granica gore je bolje za minus, granica dole je gore za minus. Kad minus poskupi (kvota raste) uz istu granicu, kladionica više očekuje plus.</p>' +
        '<div class="facts"><div><b>' + d.up.length + '</b>granica gore</div><div><b>' + d.down.length + '</b>granica dole</div><div><b>' + d.oddsUp.length + '</b>minus poskupeo</div><div><b>' + d.oddsDown.length + '</b>minus pojeftinio</div><div><b>' + d.added.length + ' / ' + d.removed.length + '</b>nove / skinute stavke</div></div>';
      if (d.up.length) h += simpleTable('Granica podignuta (bolje za minus)', '', ['Igrač','Statistika','Granica','Kvota za minus'], d.up.map(function(x){ return row(x, 'line'); })).replace('<section class="panel">', '<div>').replace(/<\/section>$/, '</div>');
      if (d.down.length) h += simpleTable('Granica spuštena (gore za minus)', '', ['Igrač','Statistika','Granica','Kvota za minus'], d.down.map(function(x){ return row(x, 'line'); })).replace('<section class="panel">', '<div>').replace(/<\/section>$/, '</div>');
      var oc = d.oddsUp.concat(d.oddsDown);
      if (oc.length) h += simpleTable('Ista granica, druga kvota', '', ['Igrač','Statistika','Granica','Kvota za minus'], oc.map(function(x){ return row(x, 'odds'); })).replace('<section class="panel">', '<div>').replace(/<\/section>$/, '</div>');
    }
    // played vs current
    var C = {}; cur.forEach(function(x){ C[deacc(x[5]) + '|' + x[1]] = x; });
    var played = state.tickets.filter(function(t){ return t.date === day; });
    if (played.length) {
      var better = 0, worse = 0, same = 0, oddsPlus = 0, list = [], seen = {};
      played.forEach(function(t){ t.legs.forEach(function(l){
        var c = C[deacc(l.p) + '|' + l.stat]; if (!c) return;
        var k = deacc(l.p) + '|' + l.stat + '|' + l.line; if (seen[k]) return; seen[k] = 1;
        if (c[2] > l.line) { worse++; list.push([esc(l.p), STAT[l.stat], fmt(l.line, 1) + ' → ' + fmt(c[2], 1), 'kasnije bolje']); }
        else if (c[2] < l.line) { better++; list.push([esc(l.p), STAT[l.stat], fmt(l.line, 1) + ' → ' + fmt(c[2], 1), 'ranije bolje']); }
        else { same++; oddsPlus += (c[3] - l.odds); }
      }); });
      h += '<h3 style="margin:14px 0 4px">Tvoji današnji tiketi u odnosu na trenutnu ponudu</h3><p class="hint">Od ' + (better + worse + same) + ' različitih parova: granica je sada niža (bolje si prošao igrajući ranije) kod ' + better + ', viša (kasnije bi bilo bolje) kod ' + worse + ', a ista kod ' + same + '. Kod parova sa istom granicom kvota za minus se u proseku promenila za ' + (same ? (oddsPlus / same >= 0 ? '+' : '') + fmt(oddsPlus / same, 2) : '0') + '.</p>';
      if (list.length) h += simpleTable('', '', ['Igrač','Statistika','Igrano → sada','Ocena'], list).replace('<section class="panel"><h2></h2>', '<div>').replace(/<\/section>$/, '</div>');
    }
    // history by day
    var days = {}; snaps.forEach(function(x){ (days[dayOfIso(x.at)] = days[dayOfIso(x.at)] || []).push(x); });
    var hist = Object.keys(days).sort().reverse().filter(function(dd){ return days[dd].length >= 2; }).map(function(dd){
      var a = days[dd].sort(function(x, y){ return String(x.at).localeCompare(String(y.at)); }), df = offerDiff(a[0].picks, a[a.length - 1].picks);
      return [esc(dd), esc(timeOfIso(a[0].at)) + ' → ' + esc(timeOfIso(a[a.length - 1].at)), '' + df.up.length, '' + df.down.length, '' + df.oddsUp.length, '' + df.oddsDown.length];
    });
    if (hist.length) h += simpleTable('Kretanje ponude po danima', 'Kada se kroz više kola granice češće podižu nego spuštaju, isplati se igrati kasnije, i obrnuto.', ['Dan','Od → do','Granica gore','Granica dole','Minus poskupeo','Minus pojeftinio'], hist).replace('<section class="panel">', '<div>').replace(/<\/section>$/, '</div>');
    return h + '</section>';
  }
  function claudePlansHtml(){
    var L = state.claudePlans || []; if (!L.length) return '';
    return '<section class="panel"><h2>Planovi od Claude-a</h2><p class="hint">Gotovi planovi koje je Claude složio i proverio simulacijom. Učitaj plan, pogledaj ga u delu 5. Plan, pa ga kopiraj u Admiral pomoćnika kao i obično.</p>' +
      L.map(function(cp){ return '<div class="q"><div><b>' + esc(cp.label) + '</b><div class="hint" style="margin:2px 0 0">' + esc(cp.desc || '') + (cp.stats ? ' Bar jedan dobitni tiket: oko ' + pct(cp.stats.app) + ' po proceni aplikacije, ' + pct(cp.stats.market) + ' po kvotama kladionice.' : '') + '</div></div><div class="acts"><button class="btn sm primary" data-act="loadCP" data-v="' + esc(cp.id) + '">Učitaj ovaj plan</button></div></div>'; }).join('') + '</section>';
  }
  function linesHtml(){
    var C = ctx(), games = [], clubs = clubsList();
    if (C && C.el && C.el.games) games = C.el.games.map(function(g){ return {h: g.h, a: g.a, d: g.d}; });
    else if (state.sched && state.sched.games) games = state.sched.games;
    var L = (state.lines && state.lines.games) || {};
    var nm = function(c){ var x = clubs[c]; return x ? (x.abbr || x.name) : c; };
    var rows = games.slice().sort(function(a, b){ return String(a.d).localeCompare(String(b.d)); }).map(function(g){
      var k = g.h + '-' + g.a, v = L[k] || {};
      var inp = function(f, ph){ return '<input type="text" inputmode="decimal" style="width:80px;padding:4px 8px" data-ln="' + k + '" data-lf2="' + f + '" placeholder="' + ph + '" value="' + esc(v[f] != null ? v[f] : '') + '">'; };
      return '<tr><td>' + esc(String(g.d || '').slice(5, 16).replace('T', ' ')) + '</td><td>' + esc(nm(g.h)) + ' – ' + esc(nm(g.a)) + '</td><td>' + inp('total', 'ukupno') + '</td><td>' + inp('hTot', 'domaćin') + '</td><td>' + inp('aTot', 'gost') + '</td></tr>';
    }).join('');
    return '<section class="panel"><h2>Kvote utakmica</h2><p class="hint">Granice poena za utakmicu i za svaki tim. Kad su unete, očekivani učinak igrača se prilagođava onome što kladionica očekuje od tima: igrači tima od koga se očekuje manje poena češće prolaze na minus. Unesi ih ručno ili ih u Admiral pomoćniku preuzmi dugmetom „Kopiraj kvote utakmica“ (na glavnoj ponudi Evrolige) i nalepi ovde.</p>' +
      (rows ? '<div class="scroll"><table><thead><tr><th>Vreme</th><th>Utakmica</th><th>Ukupno</th><th>Domaćin</th><th>Gost</th></tr></thead><tbody>' + rows + '</tbody></table></div>' : '<p class="hint">Raspored utakmica još nije poznat. Preuzmi ponudu novim pomoćnikom.</p>') +
      '<textarea id="linesBox" style="margin-top:10px;min-height:60px" placeholder="Nalepi kvote iz Admiral pomoćnika"></textarea>' +
      '<div class="btns"><button class="btn" data-act="linesPaste">Ubaci nalepljene kvote</button><button class="btn primary" data-act="linesSave">Sačuvaj kvote utakmica</button></div></section>';
  }
  function aiContext(){
    var g = genCfg(), pool = poolList();
    var rows = pool.map(function(x){
      var A = x.avg || {}, cur = A.cur, car = A.car;
      var flags = [];
      if (x.out) flags.push('ne igra');
      if (x.inj) flags.push('povreda:' + x.inj.s);
      if (A.foul) flags.push('faulovi u prošloj');
      if (x.cx && x.cx.b > 1.02) flags.push('više minuta zbog povreda +' + Math.round((x.cx.b - 1) * 100) + '%');
      if (x.cx && x.cx.gp) flags.push(x.cx.gp < 0.985 ? 'spor meč' : x.cx.gp > 1.015 ? 'brz meč' : 'prosečan tempo');
      if (x.cx && x.cx.dr) flags.push(x.cx.dr < 0.975 ? 'jaka odbrana protivnika' : x.cx.dr > 1.025 ? 'slaba odbrana protivnika' : '');
      if (!car) flags.push('novajlija u EL');
      if (x.cx && x.cx.ln && x.cx.ln.teamTot != null) flags.push('tim očekuje ' + x.cx.ln.teamTot + ' poena' + (x.cx.tAvg ? ' (prosek ' + Math.round(x.cx.tAvg) + ')' : ''));
      return [x.k, x.p, x.t, x.cx && x.cx.oppName || '', x.s, x.l, x.u,
        cur ? Math.round(cur.v * 10) / 10 + '/' + cur.g + 'ut/' + Math.round(cur.min) + 'min' : '-',
        car ? Math.round(car.v * 10) / 10 + '/' + Math.round(car.min) + 'min' : '-',
        x.mean != null ? Math.round(x.mean * 10) / 10 : '-', A.minP != null ? Math.round(A.minP) : '-', Math.round(x.pr * 100), flags.filter(function(f){ return f; }).join(', ')].join(' | ');
    });
    var set = {mix: g.mix, total: g.total, maxUse: g.maxUse, maxPl: g.maxPl, gameShare: g.gameShare, maxTeam: g.maxTeam, minOdds: g.minOdds, maxOdds: g.maxOdds, stats: g.stats, focus: g.focus, needAbove: g.needAbove, rot: g.rot, balance: g.balance, strong: g.strong, stackN: g.stackN, stackK: g.stackK};
    return {rows: rows, set: set};
  }
  function aiPrompt(text){
    var c = aiContext();
    return 'Ti si pomoćnik u aplikaciji za praćenje klađenja na Evroligu. Korisnik igra isključivo minuse (ispod granice) na poene (P), skokove (S) i asistencije (A) igrača, na tiketima od više parova. ' +
      'Na osnovu njegovog uputstva podesi generator tiketa. Ne izmišljaj parove: koristi samo ključeve iz liste.\n\n' +
      'Kolone liste: ključ | igrač | tim | protivnik | statistika | linija | kvota | ova sezona (prosek/utakmica/minuta) | prethodne tri sezone (prosek/minuta) | očekivano | očekivani minuti | šansa za minus u % | napomene\n' +
      c.rows.join('\n') + '\n\n' +
      'Trenutna podešavanja: ' + JSON.stringify(c.set) + '\n\n' +
      'Uputstvo korisnika: ' + text + '\n\n' +
      'Vrati samo JSON, bez ikakvog drugog teksta, ovog oblika (sva polja su opciona, izostavi ono što ne menjaš):\n' +
      '{"settings":{"mix":[{"legs":8,"n":10}],"total":2000,"maxUse":6,"maxPl":20,"gameShare":50,"maxTeam":3,"minOdds":1.7,"maxOdds":null,"stats":{"P":true,"A":true,"S":true},"focus":"sansa","needAbove":true,"rot":true,"balance":true,"strong":true,"stackN":0,"stackK":4},' +
      '"exclude":["ključ"],"only":["ključ"],"prefer":["ključ"],"avoid":["ključ"],"forced":["ključ"],"generate":true,"explanation":"kratko objašnjenje na srpskom, najviše 4 rečenice"}\n' +
      '"only" znači da u tikete ulaze samo navedeni parovi. "prefer" daje parovima prednost, a "avoid" ih koristi ređe. "forced" stavlja par na svaki tiket: NIKAD ga ne koristi osim ako korisnik izričito napiše da par mora biti na svakom tiketu. Kad korisnik traži više ponavljanja najizglednijih igrača, koristi "prefer" i po potrebi povećaj maxUse, a ne "forced". ' +
      'Korisnik želi prednost za igrače sa manje minuta i za sporije timove koji su dosad bili dosledni u minusu, a manje glavne igrače i timove od kojih se očekuje mnogo poena. ' +
      'Stalna pravila korisnika: najmanja kvota je 1.70 (ne spuštaj minOdds ispod 1.70 osim ako korisnik to izričito traži u ovom uputstvu); tiketi treba da budu što raznovrsniji i nijedan igrač ne sme biti na svim tiketima; maxPl je najveći procenat tiketa na kojima jedan igrač sme da bude (podrazumevano 20); gameShare je najveći procenat tiketa na kojima sme da bude jedna utakmica (podrazumevano 50), da posle prve utakmice ne bi pala većina tiketa. ' +
      'Pazi da uz izabrane parove, broj ponavljanja i najviše igrača iz istog tima može da se složi traženi broj tiketa (isti igrač ne sme dva puta na isti tiket). Ako nešto od traženog nije moguće, objasni to u polju explanation. "generate" postavi na true ako korisnik želi tikete odmah.';
  }
  function aiApply(r){
    var g = genCfg(), keys = {}, ch = [];
    poolList().forEach(function(x){ keys[x.k] = 1; });
    var prev = clone(g); ui.aiPrev = prev;
    var st2 = r && r.settings || {};
    if (Array.isArray(st2.mix) && st2.mix.length) { g.mix = st2.mix.map(function(m){ return {legs: String(m.legs), n: String(m.n)}; }); ch.push('raspodela tiketa'); }
    var LBL = {total: 'ukupan ulog', maxUse: 'ponavljanje po paru', maxPl: 'najviše tiketa po igraču', gameShare: 'najviše tiketa po utakmici', maxTeam: 'igrači iz istog tima', minOdds: 'najmanja kvota', maxOdds: 'najveća kvota', stackN: 'tiketi oko jedne utakmice', stackK: 'parovi iz iste utakmice', needAbove: 'granica iznad očekivanog', rot: 'prednost rotaciji', balance: 'ujednačavanje', strong: 'zvezdice'};
    ['total','maxUse','maxPl','gameShare','maxTeam','minOdds','maxOdds','stackN','stackK'].forEach(function(k){ if (k in st2) { g[k] = st2[k] == null ? '' : String(st2[k]); ch.push(LBL[k]); } });
    ['needAbove','rot','balance','strong'].forEach(function(k){ if (typeof st2[k] === 'boolean') { g[k] = st2[k]; ch.push(LBL[k]); } });
    if (st2.focus === 'sansa' || st2.focus === 'vrednost') { g.focus = st2.focus; ch.push('fokus'); }
    if (st2.stats && typeof st2.stats === 'object') { ['P','A','S'].forEach(function(s2){ if (typeof st2.stats[s2] === 'boolean') g.stats[s2] = st2.stats[s2]; }); ch.push('statistike'); }
    var ok = function(a){ return Array.isArray(a) ? a.filter(function(k){ return keys[k]; }) : []; };
    var ex = ok(r.exclude), only = ok(r.only), pr = ok(r.prefer), av = ok(r.avoid), fo = ok(r.forced);
    if (only.length) { g.excl = {}; Object.keys(keys).forEach(function(k){ if (only.indexOf(k) < 0) g.excl[k] = true; }); }
    ex.forEach(function(k){ g.excl[k] = true; delete g.forced[k]; });
    g.pref = {}; pr.forEach(function(k){ g.pref[k] = 1.8; }); av.forEach(function(k){ g.pref[k] = 0.4; });
    fo.forEach(function(k){ g.forced[k] = true; delete g.excl[k]; });
    ui.aiRes = {text: String(r.explanation || ''), changes: ch, counts: {exclude: ex.length, only: only.length, prefer: pr.length, avoid: av.length, forced: fo.length}};
    if (r.generate) { ui.genErr = generatePlan(); if (!ui.genErr && ui.plan) runSim(); }
  }
  function aiRun(){
    var ta = $('#aiText'), text = ta ? ta.value.trim() : '';
    if (!text) { toast('Napiši uputstvo.'); return; }
    ui.aiText = text;
    if (!sampleFn) { ui.aiRes = {err: 'Pomoćnik za uputstva nije dostupan u ovom prikazu.'}; render(); return; }
    ui.aiBusy = true; ui.aiRes = null; render();
    sampleFn.json(aiPrompt(text), {modelTier: 'default'}).then(function(r){
      ui.aiBusy = false;
      try { aiApply(r || {}); } catch(e) { ui.aiRes = {err: 'Odgovor nije mogao da se primeni.'}; }
      saveUi(); render();
    }, function(e){
      ui.aiBusy = false; ui.aiRes = {err: 'Uputstvo nije obrađeno (' + (e && e.code || 'greška') + '). Pokušaj ponovo.'}; render();
    });
  }
  function aiHtml(){
    var r = ui.aiRes;
    var res = '';
    if (ui.aiBusy) res = '<p class="hint">Claude čita ponudu i tvoje uputstvo…</p>';
    else if (r && r.err) res = '<p class="err">' + esc(r.err) + '</p>';
    else if (r) {
      var c = r.counts || {}, bits = [];
      if (r.changes && r.changes.length) bits.push('promenjena podešavanja: ' + r.changes.join(', '));
      if (c.only) bits.push('samo ' + c.only + ' izabranih parova');
      if (c.exclude) bits.push('isključeno ' + c.exclude);
      if (c.prefer) bits.push('prednost za ' + c.prefer);
      if (c.avoid) bits.push('ređe ' + c.avoid);
      if (c.forced) bits.push('obavezno ' + c.forced);
      res = '<div class="advice" style="margin:10px 0 0"><p>' + esc(r.text || 'Uputstvo je primenjeno.') + '</p>' + (bits.length ? '<p style="color:var(--muted);font-size:13px">' + esc(bits.join('; ')) + '.</p>' : '') + '</div>' +
        (ui.aiPrev ? '<div class="btns"><button class="btn sm" data-act="aiUndo">Vrati podešavanja pre uputstva</button></div>' : '');
    }
    return '<section class="panel"><h2>Uputstvo za generator</h2><p class="hint">Napiši svojim rečima šta želiš, na primer: „Danas su samo dve utakmice. Napravi 8 tiketa po 8 parova za 800 din, izbegavaj glavne igrače Panatinaikosa jer će igrati više minuta, daj prednost klupi Makabija.“ Claude pročita ponudu sa svim podacima i podesi generator. Posle toga možeš sve ručno da proveriš i promeniš.</p>' +
      '<textarea id="aiText" placeholder="Tvoje uputstvo">' + esc(ui.aiText || '') + '</textarea>' +
      '<div class="btns"><button class="btn primary" data-act="aiRun"' + (ui.aiBusy ? ' disabled' : '') + '>' + (ui.aiBusy ? 'Obrađujem…' : 'Primeni uputstvo') + '</button></div>' + res + '</section>';
  }
  function mixSummary(g){
    var n = 0;
    g.mix.forEach(function(m){ var a = parseInt(m.n, 10), b = parseInt(m.legs, 10); if (a > 0 && b > 0) n += a; });
    var tot = num(g.total);
    var slots = 0; g.mix.forEach(function(m){ var a = parseInt(m.n, 10), b = parseInt(m.legs, 10); if (a > 0 && b > 0) slots += a * b; });
    var cap = '';
    try { var ap = activePool().length, mu = parseInt(g.maxUse, 10) || Math.max(1, Math.floor(n * (num(g.maxPl) || 100) / 100)), avgL = n ? slots / n : 0; if (ap && avgL) { var maxT = Math.floor(ap * mu / avgL); cap = ' Parova koji prolaze filtere: ' + ap + ', što uz najviše ' + mu + ' tiketa po paru daje mesta za oko ' + maxT + ' tiketa ovakve dužine.' + (maxT < n ? ' Za ' + n + ' tiketa ćeš morati da smanjiš broj tiketa ili da povećaš ponavljanje, a više ponavljanja znači da jedan promašaj obara više tiketa.' : ''); } } catch(e) {}
    return n ? 'Ukupno ' + n + ' tiketa' + (tot > 0 ? ', ulog po tiketu ' + fmt(Math.floor(tot / n), 0) + ' din' : '') + '.' + cap : '';
  }
  function roleHtml(x){
    var R = {start: 'starter', rot: 'rotacija', klupa: 'rezervista', dno: 'kraj klupe'}, ms = x.ms, b = x.cx ? x.cx.b : 1, bits = [];
    bits.push(x.role ? R[x.role] + ' (' + Math.round(x.mpM) + ' min)' : 'minutaža nepoznata');
    if (ms && ms.cv != null) bits.push((x.unst ? 'nestabilni minuti ' : ms.cv <= 0.2 ? 'stabilni minuti ' : 'minuti ') + Math.round(ms.lo) + '–' + Math.round(ms.hi));
    else if (ms) bits.push('premalo utakmica');
    if (x.weak) bits.push((x.cx.posWho && x.cx.posWho.length ? 'oslabljena pozicija (ne igra ' + x.cx.posWho.join(', ') + ')' : 'tim bez više igrača') + ', očekivano +' + Math.round((b - 1) * 100) + '% minuta');
    else if (b >= 1.04) bits.push('saigrači odsutni, +' + Math.round((b - 1) * 100) + '% minuta');
    var a = x.adj, kb = [];
    if (a) {
      var PN = {G: 'bekove', F: 'krila', C: 'centre'}, SN = {P: 'poene', S: 'skokove', A: 'asistencije'};
      if (a.of != null && Math.abs(a.of - 1) >= 0.04) kb.push((a.of < 1 ? 'protivnik dobro brani ' : 'protivnik slabo brani ') + (PN[a.pos] || 'tu poziciju') + ' za ' + SN[x.s] + ' (' + (a.of > 1 ? '+' : '−') + Math.round(Math.abs(a.of - 1) * 100) + '%)');
      if (a.pace != null && a.pace >= 1.04) kb.push('brz meč, tim očekuje mnogo poena');
      else if (a.pace != null && a.pace <= 0.96) kb.push('spor meč, tim očekuje malo poena');
      if (a.close) kb.push('tesan meč');
      else if (a.spread != null) kb.push(a.spread > 0 ? 'favorit (+' + Math.round(a.spread) + ')' : 'autsajder (' + Math.round(a.spread) + ')');
      if (a.taA && Math.abs(a.taA - 1) >= 0.05) kb.push('protivnik ukupno dozvoljava ' + (a.taA < 1 ? 'malo' : 'mnogo') + ' asistencija (' + (a.taA > 1 ? '+' : '−') + Math.round(Math.abs(a.taA - 1) * 100) + '%)');
      if (a.hot) kb.push('vruća forma u poslednje 3 utakmice');
      if (a.dogB) kb.push('rezervista autsajdera, više minuta ako se meč reši');
    }
    var tag = x.cls === 'A' ? '<span class="tag dobro">više tiketa</span>' : x.cls === 'C' ? '<span class="tag lose">malo tiketa</span>' : '<span class="tag neutral">srednje</span>';
    return tag + '<br><small style="color:var(--muted)">' + esc(bits.join(', ')) + '</small>' + (kb.length ? '<br><small class="' + (a.dz > 0.02 ? 'pos' : a.dz < -0.02 ? 'neg' : '') + '" title="Kontekst utakmice: ' + (a.dz > 0 ? '+' : '') + fmt(a.dz * 100 / 4, 1) + ' procentnih poena šanse">' + esc('Kontekst: ' + kb.join(', ')) + '</small>' : '');
  }
  function viewGen(){
    var g = genCfg(), off = getOffer(), pool = poolList();
    var nPlayers = {}; (off && off.picks || []).forEach(function(x){ nPlayers[x.p] = 1; });
    var offTxt = off && off.picks ? 'Učitana ponuda: ' + off.picks.length + ' linija za ' + Object.keys(nPlayers).length + ' igrača' + (off.picks[0] && off.picks[0].time ? ', prvi meč ' + esc(off.picks[0].time) : '') + '.' : 'Ponuda još nije učitana.';
    var h = '<section class="panel"><h2>1. Ponuda</h2><p class="hint">' + offTxt + ' Novu ponudu preuzmeš dugmetom „Kopiraj ponudu“ u Admiral pomoćniku (uputstvo je na dnu) i nalepiš ovde.</p>' +
      '<textarea id="offerBox" placeholder="Nalepi ponudu iz Admiral pomoćnika"></textarea><div class="btns"><button class="btn" data-act="loadOffer">Učitaj ponudu</button></div></section>';

    h += '<section class="panel"><h2>2. Primeri</h2><p class="hint">Klik na primer popunjava podešavanja ispod. Posle ih možeš menjati.</p>' +
      Object.keys(PRESETS).map(function(k){ var p = PRESETS[k]; return '<div style="display:flex;gap:10px;align-items:baseline;padding:6px 0;border-top:1px solid var(--line)"><button class="btn sm" data-act="preset" data-v="' + k + '">' + p.label + '</button><span class="hint" style="margin:0">' + p.desc + '</span></div>'; }).join('') + '</section>';

    h += claudePlansHtml();
    h += offerMovesHtml();
    h += linesHtml();
    h += aiHtml();
    h += '<section class="panel"><h2>3. Podešavanja</h2>' +
      '<div style="margin-bottom:12px"><div class="legs-head" style="display:grid;grid-template-columns:1fr 1fr 36px;gap:8px"><span>Parova po tiketu</span><span>Broj tiketa</span><span></span></div>' +
      g.mix.map(function(m, i){ return '<div style="display:grid;grid-template-columns:1fr 1fr 36px;gap:8px;margin-bottom:6px"><input type="text" inputmode="numeric" aria-label="Parova po tiketu" data-gm="legs" data-i="' + i + '" value="' + esc(m.legs) + '"><input type="text" inputmode="numeric" aria-label="Broj tiketa" data-gm="n" data-i="' + i + '" value="' + esc(m.n) + '"><button class="x" aria-label="Ukloni red" data-act="delMix" data-i="' + i + '">×</button></div>'; }).join('') +
      '<div class="btns" style="margin-top:4px"><button class="btn sm" data-act="addMix">Dodaj red</button><span class="hint" id="mixSum" style="margin:0;align-self:center">' + mixSummary(g) + '</span></div></div>' +
      '<div class="row3">' +
      '<label class="f">Ukupan ulog (din)<input type="text" inputmode="decimal" data-g="total" value="' + esc(g.total) + '"></label>' +
      '<label class="f">Svaka utakmica najviše na (% tiketa)<input type="text" inputmode="numeric" data-g="gameShare" placeholder="npr. 50" value="' + esc(g.gameShare) + '"></label>' +
      '<label class="f">Najmanje tiketa po igraču (pokrivenost)<input type="text" inputmode="numeric" data-g="minCov" placeholder="npr. 2" value="' + esc(g.minCov) + '"></label>' +
      '<label class="f">Najviše tiketa po igraču ukupno (% tiketa)<input type="text" inputmode="numeric" data-g="maxPl" placeholder="npr. 50" value="' + esc(g.maxPl) + '"></label>' +
      '<label class="f">Najviše tiketa po paru (igrač i statistika)<input type="text" inputmode="numeric" data-g="maxUse" placeholder="kao po igraču" value="' + esc(g.maxUse) + '"></label>' +
      '<label class="f">Najviše igrača iz istog tima na tiketu<input type="text" inputmode="numeric" data-g="maxTeam" placeholder="bez ograničenja" value="' + esc(g.maxTeam) + '"></label>' +
      '<label class="f">Kvota po paru od<input type="text" inputmode="decimal" data-g="minOdds" placeholder="npr. 1.80" value="' + esc(g.minOdds) + '"></label>' +
      '<label class="f">Kvota po paru do<input type="text" inputmode="decimal" data-g="maxOdds" placeholder="npr. 2.10" value="' + esc(g.maxOdds) + '"></label>' +
      '<label class="f">Kolo (za upis tiketa)<input type="text" data-g="round" placeholder="npr. 2" value="' + esc(g.round) + '"></label>' +
      '<label class="f">Novac za ove tikete<select data-g="fund"><option value="novi"' + (g.fund !== 'dobitak' ? ' selected' : '') + '>Svež novac</option><option value="dobitak"' + (g.fund === 'dobitak' ? ' selected' : '') + '>Iz dobitka</option></select></label></div>' +
      '<div class="filters">' + ['P','A','S'].map(function(st){ return '<label class="cb"><input type="checkbox" data-gs="' + st + '"' + (g.stats[st] ? ' checked' : '') + '>' + STAT[st] + '</label>'; }).join(' ') + '</div>' +
      '<div style="display:flex;flex-direction:column;gap:8px">' +
      '<label class="cb"><input type="checkbox" data-g="balance"' + (g.balance ? ' checked' : '') + '>Ujednači ponavljanja: svi izbori se pojavljuju približno isti broj puta</label>' +
      '<label class="cb"><input type="checkbox" data-g="strong"' + (g.strong ? ' checked' : '') + '>Najbolje procenjenim izborima (★) dozvoli više ponavljanja, do granice iz polja „Najviše tiketa po paru“</label>' +
      '<label class="cb"><input type="checkbox" data-g="rot"' + (g.rot ? ' checked' : '') + '>Ponavljaju se rezervisti: igrači do 25 minuta sa stabilnom minutažom mogu na najviše tiketa (do granice po igraču). Starteri (25+ minuta) i igrači čija se minutaža još ne zna idu na oko 60% te granice. Igrači sa nestabilnom minutažom, sa manje od 12 minuta i oni na oslabljenoj poziciji (ne igra saigrač na istoj poziciji) idu na najviše trećinu.</label>' +
      '<label class="cb"><input type="checkbox" data-g="best"' + (g.best ? ' checked' : '') + '>Za svakog igrača samo njegova najjača stavka (poeni, skokovi ili asistencije, ona sa najvećom šansom)</label>' +
      '<label class="cb"><input type="checkbox" data-g="opt"' + (g.opt ? ' checked' : '') + '>Optimizuj za najveći procenat dobitnih tiketa. Generator hiljadama zamena traži raspored sa najviše očekivanih dobitnih tiketa, uz prednost rasporedu u kome bar jedan tiket prolazi u što više slučajeva. Pokrivenost (bar zadati broj tiketa po igraču) važi za jačih 60% izbora.</label>' +
      '<label class="cb"><input type="checkbox" data-g="needAbove"' + (g.needAbove ? ' checked' : '') + '>Samo parovi gde je granica iznad očekivanog (za poene bar 1 poen, za skokove i asistencije bar 0,4)</label>' +
      '<label class="cb"><input type="checkbox" data-g="onlyPos"' + (g.onlyPos ? ' checked' : '') + '>Koristi samo parove sa vrednošću „Dobar“ ili „Vrlo dobar“</label>' +
      '<label class="f" style="flex-direction:row;align-items:center;gap:8px;max-width:520px">Fokus generatora <select data-g="focus" style="width:auto"><option value="sansa"' + (g.focus !== 'vrednost' ? ' selected' : '') + '>Najizgledniji parovi (najveća šansa)</option><option value="vrednost"' + (g.focus === 'vrednost' ? ' selected' : '') + '>Najbolja vrednost (šansa u odnosu na kvotu; ne preporučuje se, u proveri posle 7. kola nije razlikovala dobre i loše parove)</option></select></label></div>' +
      '<div class="row3" style="margin-top:12px">' +
      '<label class="f">Tiketa oko jedne utakmice<input type="text" inputmode="numeric" data-g="stackN" value="' + esc(g.stackN) + '"></label>' +
      '<label class="f">Parova iz te utakmice na tiketu<input type="text" inputmode="numeric" data-g="stackK" value="' + esc(g.stackK) + '"></label>' +
      '<label class="f">Budžet po kolu (din)<span style="display:flex;gap:6px"><input type="text" inputmode="decimal" id="budgetIn" placeholder="bez budžeta" value="' + esc(state.settings && state.settings.budget ? state.settings.budget : '') + '"><button class="btn sm" data-act="saveBudget">Sačuvaj</button></span></label></div>' +
      '<p class="hint">„Tiketa oko jedne utakmice“: toliko tiketa dobija bar zadati broj parova iz iste utakmice (oba tima), da bi se kroz kola videlo da li takvi tiketi prolaze češće. Ostali tiketi se slažu kao i do sada. Uz 0 ova opcija je isključena.</p>' +
      '<p class="hint" style="margin-top:10px">Isti igrač nikad nije dva puta na istom tiketu. Ograničenje igrača iz istog tima smanjuje rizik da jedna utakmica obori ceo tiket: kad tim loše krene, obično svi njegovi igrači podbace zajedno.</p></section>';

    h += injuryHtml(off);
    var C = ctx();
    if (!C) {
      if (off && off.picks) h += '<section class="panel"><h2>Protivnici i odsustva</h2><p class="hint">Ova ponuda je preuzeta bez statistike sa Evrolige. Za protivnike, odbrane, odsustva i sveže proseke preuzmi ponudu ponovo, dugmetom „Kopiraj ponudu i statistiku“ u novoj verziji Admiral pomoćnika.</p></section>';
    } else {
      var TN = {}; Object.keys(C.el.tmap).forEach(function(t){ TN[C.el.tmap[t]] = t; });
      var candRows = C.cand.slice().sort(function(a, b){ return (a.club || '').localeCompare(b.club || '') || b.m - a.m; }).map(function(c){
        return '<tr><td><label class="cb"><input type="checkbox" data-abs="' + esc(c.k) + '" data-auto="' + (c.auto ? 1 : 0) + '"' + (c.on ? ' checked' : '') + '>Ne igra</label></td><td>' + esc(c.name) + '</td><td>' + esc(TN[c.club] || c.club) + '</td><td>' + esc(({Guard: 'bek', Forward: 'krilo', Center: 'centar'})[c.pos] || c.pos || '') + '</td><td class="r">' + fmt(c.m, 0) + ' min</td><td>' + esc(c.why || (c.auto ? 'nema ga u ponudi' : 'dodato ručno')) + '</td></tr>';
      }).join('');
      var rosterOpts = [];
      Object.keys(C.el.tmap).forEach(function(t){ (C.el.rosters[C.el.tmap[t]] || []).forEach(function(r){ rosterOpts.push('<option value="' + esc(prettyName(r[2])) + ' (' + esc(t) + ')">'); }); });
      var games = (C.el.games || []).filter(function(gm){ return TN[gm.h] || TN[gm.a]; }).map(function(gm){ var ch = C.el.clubs[gm.h] || {}, ca = C.el.clubs[gm.a] || {}; return esc(ch.abbr || ch.name || gm.h) + ' – ' + esc(ca.abbr || ca.name || gm.a); });
      h += '<section class="panel"><h2>Protivnici i odsustva</h2><p class="hint">Utakmice: ' + games.join(', ') + '. Statistika preuzeta ' + esc(String(C.el.at || '').slice(0, 16).replace('T', ' ')) + '.</p>' +
        '<p class="hint">Igrači koji inače igraju bar 18 minuta, a nema ih u ponudi kladionice, verovatno ne igraju (povreda, odmor). Kladionica obično skida ponudu za igrače koji neće igrati. Njihovi minuti se raspoređuju saigračima, više onima na istoj poziciji, pa minus saigrača postaje rizičniji. Isključi kvačicu ako znaš da igrač ipak igra, ili dodaj ručno nekoga ko ne igra.</p>' +
        (candRows ? '<div class="scroll"><table class="sortable" data-sid="gen-abs">' + sortHead(['', 'Igrač', 'Tim', 'Pozicija', 'Minuta', 'Razlog'], 4) + '<tbody>' + candRows + '</tbody></table></div>' : '<p class="hint">Nema igrača iz rotacije koji nedostaju u ponudi.</p>') +
        '<div style="display:flex;gap:8px;margin-top:10px;flex-wrap:wrap"><input type="text" id="absAdd" list="dl-roster" placeholder="Dodaj igrača koji ne igra" style="max-width:320px"><button class="btn" data-act="absAdd">Dodaj</button></div><datalist id="dl-roster">' + rosterOpts.join('') + '</datalist>' +
        '<p class="hint" style="margin-top:10px">Tačan izveštaj o povredama Evroliga ne objavljuje u obliku koji aplikacija može da pročita, pa je ovo procena. Za sigurniju listu pitaj Claude-a u razgovoru pre kola da proveri vesti.</p></section>';
    }

    if (pool.length) {
      var UNIT = {P: 'poena', S: 'skokova', A: 'asist.'};
      var rows = pool.map(function(x){
        var on = !g.excl[x.k], fo = !!g.forced[x.k], A = x.avg, mnO = num(g.minOdds), mxO = num(g.maxOdds);
        var why = fo ? '' : x.out ? 'ne igra' : g.best && x.alt && on ? 'slabija stavka istog igrača (jača: ' + STAT[x.altOf] + ')' : !g.stats[x.s] ? '' : mnO && x.u < mnO ? 'kvota ispod ' + fmt(mnO) : mxO && x.u > mxO ? 'kvota iznad ' + fmt(mxO) : g.needAbove && !x.okAbove && !g.opt ? 'granica nije dovoljno iznad očekivanog' : '';
        return '<tr' + (why ? ' style="opacity:.5" title="Ne ulazi u tikete: ' + esc(why) + '"' : '') + '><td><label class="cb" title="Uključi"><input type="checkbox" data-gx="' + esc(x.k) + '"' + (on || fo ? ' checked' : '') + '></label></td>' +
          '<td><label class="cb" title="Obavezno na svakom tiketu"><input type="checkbox" data-gf="' + esc(x.k) + '"' + (fo ? ' checked' : '') + '></label></td>' +
          '<td data-v="' + esc(deacc(x.p)) + '">' + (x.strong ? '★ ' : '') + esc(x.p) + (x.inj ? '<br><span class="tag ' + (x.inj.s === 'out' ? 'lose' : 'neutral') + '" title="' + esc(x.inj.note || '') + '">' + INJ_TXT[x.inj.s] + '</span>' : '') + (why ? '<br><small style="color:var(--muted)">ne ulazi: ' + esc(why) + '</small>' : '') + '</td>' +
          '<td>' + esc(x.t) + (x.cx && x.cx.pos ? '<br><small style="color:var(--muted)">' + esc(({Guard: 'bek', Forward: 'krilo', Center: 'centar'})[x.cx.pos] || x.cx.pos) + '</small>' : '') + '</td>' +
          '<td data-v="' + (x.cx && x.cx.ratio ? x.cx.ratio : '') + '">' + (x.cx && x.cx.opp ? esc(x.cx.oppName) + (x.cx.ratio ? '<br><small class="' + cls(1 - x.cx.ratio) + '">' + (x.cx.ratio < 1 ? 'dozvoljava ' + fmt((1 - x.cx.ratio) * 100, 0) + '% manje' : 'dozvoljava ' + fmt((x.cx.ratio - 1) * 100, 0) + '% više') + '</small>' : '') : '–') + '</td>' +
          '<td>' + STAT[x.s] + (x.out ? '<br><small class="neg">ne igra</small>' : '') + '</td>' +
          '<td class="r" data-v="' + x.l + '">' + fmt(x.l, 1) + '</td>' +
          '<td class="r" data-v="' + x.u + '">' + fmt(x.u) + '</td>' +
          '<td class="r" data-v="' + (A && A.cur ? A.cur.v : '') + '">' + (A && A.cur ? '<b>' + fmt(A.cur.v, 1) + '</b> ' + UNIT[x.s] + '<br><small style="color:var(--muted)">' + A.cur.g + ' ut., ' + Math.round(A.cur.min) + ' min</small>' : '<small style="color:var(--muted)">još nije igrao</small>') + '</td>' +
          '<td class="r" data-v="' + (A && A.car ? A.car.v : '') + '">' + (A && A.car ? fmt(A.car.v, 1) + ' ' + UNIT[x.s] + '<br><small style="color:var(--muted)">' + A.car.g + ' ut., ' + Math.round(A.car.min) + ' min</small>' : '<small style="color:var(--muted)">nema u EL</small>') + '</td>' +
          '<td class="r" data-v="' + (x.mean != null ? x.mean : '') + '">' + (x.mean != null ? '<b>' + fmt(x.mean, 1) + '</b><br><small style="color:var(--muted)">' + (A.wcur >= 0.5 ? 'sezona' : A.wcur > 0 ? 'sezona i prošle 3' : 'prošle 3 sezone') + (x.cx && x.cx.gp ? (x.cx.gp < 0.985 ? ', spor meč' : x.cx.gp > 1.015 ? ', brz meč' : '') : '') + (x.cx && x.cx.dr ? (x.cx.dr < 0.975 ? ', jaka odbrana' : x.cx.dr > 1.025 ? ', slaba odbrana' : '') : (x.cx && Math.abs(x.cx.f - 1) >= 0.02 ? ', odbrana ' + (x.cx.f > 1 ? '+' : '') + fmt((x.cx.f - 1) * 100, 0) + '%' : '')) + (x.cx && x.cx.ln && x.cx.ln.teamTot != null ? ', tim očekuje ' + fmt(x.cx.ln.teamTot, 1) + (x.cx.tAvg ? ' (prosek ' + fmt(x.cx.tAvg, 0) + ')' : '') : '') + (x.cx && x.cx.b > 1.02 ? ', minuti +' + fmt((x.cx.b - 1) * 100, 0) + '% (povrede)' : '') + (A.foul ? ', faulovi u prošloj utakmici: računato sa uobičajenom minutažom' : '') + '</small>' : '–') + '</td>' +
          '<td class="r" data-v="' + (x.mean != null ? x.l - x.mean : '') + '">' + (x.mean != null ? '<span class="' + cls(x.l - x.mean) + '">' + (x.l - x.mean > 0 ? '+' : '') + fmt(x.l - x.mean, 1) + '</span>' : '–') + '</td>' +
          '<td class="r" data-v="' + x.pr + '">' + pct(x.pr) + '</td>' +
          '<td data-v="' + x.ev + '">' + meter(x.ev) + (x.np ? ' <small style="color:var(--muted)">tvoji: ' + x.hp + '/' + x.np + '</small>' : '') + '</td>' +
          '<td data-v="' + ({A: 1, B: 2, C: 3})[x.cls] + '">' + roleHtml(x) + '</td></tr>';
      }).join('');
      h += '<section class="panel"><h2>4. Izbori</h2>' +
        '<details style="margin-bottom:10px"><summary style="cursor:pointer;font-weight:600">Kako se čita tabela</summary><div class="hint" style="margin-top:8px">' +
        '<p><b>Ova sezona</b> je prosek igrača u Evroligi ove sezone za tu statistiku (poeni, skokovi ili asistencije), sa brojem utakmica i prosečnom minutažom. Ovo je glavni podatak za odluku. <b>Prošle 3 sezone EL</b> je prosek iz poslednje tri evroligaške sezone, gde se novija sezona računa više. Starije sezone se ne računaju, jer igrač koji je u Evroligi igrao pre deset godina danas može biti sasvim drugačiji igrač.</p>' +
        '<p><b>Protivnik</b> je ekipa protiv koje igrač igra u ovom kolu. Ispod piše koliko ta ekipa dozvoljava poena, skokova ili asistencija u odnosu na prosek lige. „Dozvoljava 6% manje“ znači jaču odbranu za tu statistiku, što ide u korist minusu.</p>' +
        '<p><b>Očekivano</b> je koliko bi igrač mogao da ostvari: prosek (na početku sezone uglavnom iz prošle tri sezone, a sa svakim kolom sve više iz ove sezone; posle 4 utakmice ova sezona vredi koliko prethodne tri), pomeren za odbranu protivnika i za dodatne minute ako neko iz njegovog tima ne igra. Ispod broja piše šta je uračunato. <b>Linija − očekivano</b>: zeleni plus znači da je granica iznad očekivanog, što ide u korist minusu.</p>' +
        '<p><b>Kako se računa očekivano:</b> učinak po minutu (ova sezona i prethodne tri) puta očekivani minuti. Ako je igrač u prošloj utakmici igrao manje zbog 4 ili više faula, računa se sa njegovom uobičajenom minutažom, jer će verovatno igrati duže. Zatim se uračunavaju ritam utakmice (sporiji meč znači manje napada, pa manje poena, skokova i asistencija), odbrana protivnika i dodatni minuti zbog povreda saigrača.</p>' +
        '<p><b>Šansa</b> je procenjena verovatnoća da minus prođe. Po njoj ređaj kad tražiš najsigurnije parove. <b>Vrednost</b> je ocena od „Loš“ do „Vrlo dobar“ koja poredi tu šansu sa kvotom: par sa šansom od 52% i kvotom 2,02 ima dobru vrednost, iako nije siguran, a par sa šansom od 62% i kvotom 1,52 može imati lošu vrednost, iako češće prolazi. Šansa se računa po pravilima iz analize svih ponuda ove sezone: osnova su kvote za manje i više; asistencije, skokovi i poeni sa granicom od 10,5 naviše prolaze češće; igrači sa 21 i više minuta češće od onih sa malo minuta; nestabilna minutaža i oslabljena pozicija (saigrač iste pozicije ne igra) obaraju šansu; očekivano iz proseka i protivnika ima manju težinu. Od 24.10. računa se i kontekst utakmice: protivnik koji dobro brani igračevu poziciju (bekove, krila ili centre) i spor meč sa malo očekivanih poena tima (iz kvota utakmica, a bez njih iz proseka timova) podižu šansu; tesan meč (razlika do 5 poena) podiže; vruća forma u poslednje 3 utakmice i rezervista ekipe koja je autsajder obaraju. Sve to piše u koloni Uloga, u redu „Kontekst“. Tvoji dosadašnji rezultati po igraču se više ne računaju, jer posle sedam kola nisu ništa predviđali. Više crtica znači bolji par za minus. Ocena nije garancija: kladionica ima više podataka (povrede, minutaža, protivnik), pa je „Prosečan“ sasvim normalna ocena za većinu parova.</p>' +
        '<p><b>Uloga i ponavljanje</b>: starter (25+ minuta), rotacija (21 do 25), rezervista (12 do 21) ili kraj klupe (ispod 12), i koliko varira minutaža po utakmicama ove sezone. „Više tiketa“ dobijaju igrači do 25 minuta sa stabilnom minutažom, „srednje“ starteri i igrači bez dovoljno utakmica, a „malo tiketa“ nestabilni, igrači sa malo minuta i oni na oslabljenoj poziciji.</p>' +
        '<p><b>★</b> označava petinu parova sa najboljom ocenom u ovoj ponudi. <b>Obavezno</b> stavlja par na svaki tiket. Koristi ga retko, jer ako takav par padne, padaju svi tiketi. Klikom na naslov kolone tabela se ređa po toj koloni.</p></div></details>' +
        '<div class="btns" style="margin-top:0"><button class="btn sm" data-act="exclAll">Isključi sve</button><button class="btn sm" data-act="inclAll">Uključi sve</button></div>' +
        '<div class="scroll"><table class="sortable" data-sid="gen-pool"><thead><tr><th data-col="0">Uklj.</th><th data-col="1">Obav.</th><th data-col="2">Igrač</th><th data-col="3">Tim</th><th data-col="4">Protivnik</th><th data-col="5">Statistika</th><th data-col="6" class="r">Linija</th><th data-col="7" class="r">Kvota</th><th data-col="8" class="r">Ova sezona</th><th data-col="9" class="r">Prošle 3 sezone EL</th><th data-col="10" class="r">Očekivano</th><th data-col="11" class="r">Linija − očekivano</th><th data-col="12" class="r">Šansa</th><th data-col="13">Vrednost</th><th data-col="14">Uloga i ponavljanje</th></tr></thead><tbody>' + rows + '</tbody></table></div>' +
        (ui.genErr ? '<div class="err" role="alert">' + esc(ui.genErr) + '</div>' : '') +
        '<div class="btns"><button class="btn primary" data-act="generate"' + (ui.genBusy ? ' disabled' : '') + '>' + (ui.genBusy ? 'Generišem i optimizujem…' : ui.plan ? 'Generiši ponovo' : 'Generiši tikete') + '</button></div></section>';
    }

    if (ui.plan) {
      var p = ui.plan, uses = {}, info = {};
      p.tickets.forEach(function(t){ t.legs.forEach(function(l){ var k = l.c + l.s; uses[k] = (uses[k] || 0) + 1; info[k] = l; }); });
      var totalStake = p.tickets.reduce(function(a, t){ return a + t.stake; }, 0);
      var probs = p.tickets.map(function(t){ return t.legs.reduce(function(a, l){ return a * (l.pr || 0.5); }, 1); });
      var odds = p.tickets.map(function(t){ return t.legs.reduce(function(a, l){ return a * l.u; }, 1); });
      var expRet = p.tickets.reduce(function(a, t, i){ return a + t.stake * odds[i] * probs[i]; }, 0);
      var avgP = probs.reduce(function(a, b){ return a + b; }, 0) / probs.length;
      var tk = p.tickets.map(function(t, i){
        return '<article class="tk"><div class="tk-b" style="padding-top:10px"><b>Tiket ' + (i + 1) + '</b>' + (t.stackLbl ? ' <span class="tag neutral">oko utakmice ' + esc(t.stackLbl) + '</span>' : '') + ' <span style="color:var(--muted)">' + parova(t.legs.length) + ', ulog ' + fmt(t.stake) + ', kvota ' + fmt(odds[i]) + ', procena prolaza ' + pct(probs[i]) + '</span><div style="font-size:14px;margin-top:4px">' +
          t.legs.map(function(l){ return (l.f ? '<b>' : '') + esc(l.p) + ' ' + l.s + ' &lt;' + fmt(l.l, 1) + ' @' + fmt(l.u) + (l.f ? '</b>' : ''); }).join(', ') + '</div></div></article>';
      }).join('');
      var bySize = {};
      p.tickets.forEach(function(t, i){ var n = t.legs.length, b = bySize[n] || (bySize[n] = {c: 0, st: 0, pr: 0, ret: 0, odds: 0}); b.c++; b.st += t.stake; b.pr += probs[i]; b.ret += t.stake * odds[i] * probs[i]; b.odds += odds[i]; });
      var sizeRows = Object.keys(bySize).sort(function(a, b){ return a - b; }).map(function(n){ var b = bySize[n]; return [n, '' + b.c, fmt(b.st), fmt(b.odds / b.c), pct(b.pr / b.c), fmt(b.ret) + ' <small style="color:var(--muted)">(' + pct(b.ret / b.st) + ')</small>']; });
      var cnts = Object.keys(uses).map(function(k){ return uses[k]; });
      var minU = Math.min.apply(null, cnts), maxU = Math.max.apply(null, cnts), plT = {};
      p.tickets.forEach(function(t){ var sn = {}; t.legs.forEach(function(l){ var k = deacc(l.p); if (!sn[k]) { plT[k] = (plT[k] || 0) + 1; sn[k] = 1; } }); });
      var plCnt = Object.keys(plT).map(function(k){ return plT[k]; }), plMin = Math.min.apply(null, plCnt), plMax = Math.max.apply(null, plCnt);
      var expRows = exposureRows(p.tickets.map(function(t){ return t.legs.map(function(l){ return {p: l.p, t: l.t, s: l.s, l: l.l, st: l.st}; }); }));
      var pAt = new Date(p.at), pAtTxt = isNaN(pAt) ? '' : pAt.toLocaleString('sr-RS', {day: 'numeric', month: 'numeric', hour: '2-digit', minute: '2-digit'});
      var topPl = Object.keys(plT).sort(function(a, b){ return plT[b] - plT[a]; })[0];
      var expWarn = topPl && plT[topPl] >= Math.ceil(p.tickets.length * 0.7) && p.tickets.length >= 5 ? '<p class="hint" style="color:var(--miss);font-weight:600">Pažnja: jedan igrač je na ' + plT[topPl] + ' od ' + p.tickets.length + ' tiketa. Ako on promaši, pada skoro ceo plan.</p>' : '';
      h += '<section class="panel"><h2>5. Plan' + (p.fromClaude ? ' <small style="font-weight:400;color:var(--muted)">(' + esc(p.fromClaude) + ')</small>' : '') + '</h2>' + expWarn +
        '<p class="hint"><span class="tag ' + (p.saved ? 'hit' : 'neutral') + '">' + (p.saved ? 'Upisan kao odigran' + (p.saved.round ? ', kolo ' + esc(p.saved.round) : '') : 'Još nije upisan') + '</span> Generisan ' + esc(pAtTxt) + '. Ovo je poslednji plan generisan u ovom prozoru. Svaki klik na „Generiši ponovo“ pravi novi, drugačiji plan. Stvarno odigrane tikete vidiš u delu „Odigrano u kolu“ ispod i na kartici Tiketi.</p>' +
        (p.warn ? '<p class="hint" style="color:var(--pend)">' + esc(p.warn) + '</p>' : '') +
        (function(){ var tg = {}; p.tickets.forEach(function(t){ var sg2 = {}; t.legs.forEach(function(l){ if (l.g) sg2[l.g] = 1; }); Object.keys(sg2).forEach(function(k){ tg[k] = (tg[k] || 0) + 1; }); }); var ks = Object.keys(tg); if (!ks.length) return ''; var mx = Math.max.apply(null, ks.map(function(k){ return tg[k]; })); return '<p class="hint">Najviše tiketa zavisi od jedne utakmice: ' + mx + ' od ' + p.tickets.length + ' (' + pct(mx / p.tickets.length) + '). Toliko najviše može da padne posle prve utakmice.</p>'; })() +
        (p.opt != null ? '<p class="hint">Optimizovan raspored, po proceni generatora: ' + (p.expWins != null ? 'očekivano ' + fmt(p.expWins, 2) + ' dobitnih tiketa od ' + p.tickets.length + ' (' + pct(p.expWins / p.tickets.length) + ' po tiketu), a ' : '') + 'bar jedan tiket prolazi u oko ' + pct(p.opt) + ' slučajeva. Trezvenije brojke su u simulaciji ispod.</p>' : '') +
        '<p class="hint">' + p.tickets.length + ' tiketa, ukupno ' + fmt(totalStake) + ' din. Korišćeno je ' + cnts.length + ' parova ' + plCnt.length + ' igrača. Svaki par je na ' + (minU === maxU ? minU : minU + ' do ' + maxU) + ' tiketa, a igrač ukupno na ' + (plMin === plMax ? plMin : plMin + ' do ' + plMax) + '. Prosečna procena prolaza tiketa je ' + pct(avgP) + '. Po procenama bi se u proseku vratilo oko ' + fmt(expRet) + ' din, ali to je prosek preko mnogo kola: u pojedinačnom kolu najčešće ne prođe nijedan tiket, a ponekad prođe jedan i vrati mnogo.</p>' +
        budgetHtml(totalStake) + simHtml() +
        '<div class="btns"><button class="btn primary" data-act="copyPlan">Kopiraj plan za AdmiralBet</button><button class="btn" data-act="savePlan">Upiši u odigrane tikete</button></div>' +
        '<textarea id="planBox" readonly style="margin-top:10px;min-height:70px">' + esc(planJson()) + '</textarea>' +
        '<div style="margin-top:12px">' + tk + '</div></section>' +
        simpleTable('Po broju parova', 'Očekivani povraćaj je prosek po procenama, preko mnogo kola.', ['Parova','Tiketa','Ulog','Prosečna kvota','Procena prolaza','Očekivani povraćaj'], sizeRows) +
        simpleTable('Ponavljanje igrača u planu', 'Na koliko tiketa je svaki igrač, ukupno i po paru. „Najviše tiketa po paru“ važi za svaki par posebno (poeni, skokovi, asistencije), pa igrač ukupno može biti na više tiketa.', ['Igrač','Tiketa ukupno','Parovi (tiketa)'], expRows);
    }

    h += playedRoundHtml();
    h += '<section class="panel"><h2>6. Odigrano iz pomoćnika</h2><p class="hint">Kad složiš i uplatiš tikete, u panelu Admiral pomoćnika klikni „Kopiraj odigrano“ i nalepi ovde. Upisuju se stvarne linije i kvote sa kojima su tiketi uplaćeni, zajedno sa parovima kojima je linija podignuta. Parove koje si dodao ručno posle ispravi na kartici Tiketi.</p>' +
      '<textarea id="playedBox" placeholder="Nalepi odigrano iz Admiral pomoćnika"></textarea><div class="btns"><button class="btn primary" data-act="importPlayed">Upiši odigrano iz pomoćnika</button></div></section>';
    h += '<section class="panel"><h2>Admiral pomoćnik</h2><p class="hint">Obeleživač (bookmark) koji na AdmiralBet stranici otvara mali panel. Panel preuzima ponudu za generator, a iz plana klikće parove jednog po jednog tiketa i upisuje ulog. Uplatu uvek potvrđuješ ti, dugmetom UPLATA. Pomoćnik ne šalje podatke nikuda.</p>' +
      '<p class="hint">Postavljanje u Chrome-u:</p><ol class="hint" style="padding-left:20px"><li>Klikni „Kopiraj kod pomoćnika“ ispod.</li><li>Desni klik na traku sa obeleživačima, pa „Dodaj stranicu“ (Add page). Ako traka nije vidljiva, uključi je sa Ctrl+Shift+B.</li><li>Za ime upiši „Admiral pomoćnik“, a u polje za adresu (URL) nalepi kopirani kod i sačuvaj.</li><li>Na AdmiralBetu otvori Košarka igrači, Igrači ukupno, Evroliga i klikni obeleživač.</li></ol>' +
      '<textarea id="bmBox" readonly style="min-height:70px">' + esc(BOOKMARKLET) + '</textarea>' +
      '<div class="btns"><button class="btn" data-act="copyBm">Kopiraj kod pomoćnika</button></div>' +
      '<p class="hint">Rad sa planom: u panelu klikni „Nalepi plan“, nalepi plan i „Učitaj plan“. Zatim „Složi tiket“, proveri tiket i uplati, pa „Sledeći“ i ponovo „Složi tiket“. Ako je linija podignuta, što ide u korist minusu, par se dodaje sa novom linijom. Ako je linija spuštena, par se ne dodaje i označen je da ga proveriš ručno. Promena kvote se samo napomene. Na kraju klikni „Kopiraj odigrano“ i nalepi u deo 6.</p></section>';
    h += '<section class="panel"><h2>MaxBet pomoćnik</h2><p class="hint">Obeleživač za MaxBet. Ponudu preuzima direktno sa MaxBet servera, sa poenima, asistencijama i skokovima za sve igrače, bez klikanja, i dodaje statistiku sa Evrolige. Pomoćnik ne šalje podatke nikuda.</p>' +
      '<p class="hint">Postavljanje u Chrome-u na Macu:</p><ol class="hint" style="padding-left:20px"><li>Klikni „Kopiraj kod MaxBet pomoćnika“ ispod.</li><li>Prikaži traku sa obeleživačima (Cmd+Shift+B), desni klik na nju, pa „Add page“ (Dodaj stranicu).</li><li>Za ime upiši „MaxBet pomoćnik“, a u polje URL nalepi kopirani kod i sačuvaj.</li><li>Otvori maxbet.rs (bilo koja stranica sportskog klađenja) i klikni obeleživač, pa „Kopiraj ponudu i statistiku“. Nalepi u Generator, deo Ponuda.</li></ol>' +
      '<textarea id="bmBoxMb" readonly style="min-height:70px">' + esc(BOOKMARKLET_MB) + '</textarea>' +
      '<div class="btns"><button class="btn" data-act="copyBmMb">Kopiraj kod MaxBet pomoćnika</button></div>' +
      '<p class="hint">Rad sa planom: u panelu „Nalepi plan“, pa „Učitaj plan“. Panel prikazuje parove tiketa sa MaxBet šiframa igrača. Na kraju „Kopiraj odigrano“ i nalepi u deo 6. Na stranici Poeni igrača EUROLEAGUE (lista igrača) klikni „Složi tiket“: pomoćnik sam dodaje parove (poene iz liste, skokove i asistencije sa stranice igrača), proverava granice i upisuje ulog. Ako je granica spuštena, par ne dodaje i označi ga crveno. Uplatu potvrđuješ ti, dugmetom UPLATI, pa klikneš „Odigran ✓“.</p></section>';
    return h;
  }
  function copyText(id){
    var ta = $('#' + id); if (!ta) return;
    ta.focus(); ta.select();
    var done = function(ok){ toast(ok ? 'Kopirano.' : 'Označeno je, kopiraj sa Ctrl+C.'); };
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) { navigator.clipboard.writeText(ta.value).then(function(){ done(true); }, function(){ var ok = false; try { ok = document.execCommand('copy'); } catch(e) {} done(ok); }); return; }
    } catch(e) {}
    var ok = false; try { ok = document.execCommand('copy'); } catch(e) {} done(ok);
  }

  /* ---------- sorting ---------- */
  function cellVal(td){
    if (!td) return null;
    if (td.hasAttribute('data-v')) { var dv = td.getAttribute('data-v'); if (dv === '') return null; var nv = parseFloat(dv); return isFinite(nv) ? nv : dv.toLowerCase(); }
    var inp = td.querySelector('input');
    if (inp) { if (inp.type === 'checkbox') return inp.checked ? 1 : 0; var iv = num(inp.value); return iv == null ? null : iv; }
    var t = td.textContent.replace(/\s+/g, ' ').trim().replace(/^★\s*/, '');
    if (!t || t === '–' || t === '-') return null;
    if (/^[−+-]?\d/.test(t)) { var n2 = parseFloat(t.replace(/\./g, '').replace(',', '.').replace('−', '-')); if (isFinite(n2)) return n2; }
    return t.toLowerCase();
  }
  function sortTable(table, col, dir){
    var tb = table.tBodies[0]; if (!tb) return;
    var rows = Array.prototype.slice.call(tb.rows).map(function(r, i){ return {r: r, i: i, v: cellVal(r.cells[col])}; });
    rows.sort(function(a, b){
      var x = a.v, y = b.v;
      if (x == null && y == null) return a.i - b.i;
      if (x == null) return 1; if (y == null) return -1;
      var c = (typeof x === 'number' && typeof y === 'number') ? x - y : (typeof x === 'number' ? -1 : typeof y === 'number' ? 1 : String(x).localeCompare(String(y), 'sr', {numeric: true}));
      return (c || (a.i - b.i) * dir) * dir;
    });
    rows.forEach(function(o){ tb.appendChild(o.r); });
    Array.prototype.forEach.call(table.querySelectorAll('th[data-col]'), function(th){ th.classList.remove('asc', 'desc'); if (+th.getAttribute('data-col') === col) th.classList.add(dir > 0 ? 'asc' : 'desc'); });
  }
  function applySorts(){
    var so = ui.sorts || {};
    Array.prototype.forEach.call(document.querySelectorAll('table[data-sid]'), function(t){ var st = so[t.getAttribute('data-sid')]; if (st) sortTable(t, st.c, st.d); });
  }
  function sortHead(labels, rightFrom){
    return '<thead><tr>' + labels.map(function(h, k){ return h === null ? '<th></th>' : '<th data-col="' + k + '"' + (k >= (rightFrom == null ? 1 : rightFrom) ? ' class="r"' : '') + '>' + h + '</th>'; }).join('') + '</tr></thead>';
  }
  function sidOf(t){ return 't-' + deacc(String(t)).replace(/[^a-z0-9]+/g, '-'); }

  function render(){
    var root = $('#root');
    var view = ui.tab === 'rezultati' ? viewResults() : ui.tab === 'tiketi' ? viewTickets() : ui.tab === 'analiza' ? viewAnalysis() : ui.tab === 'generator' ? viewGen() : viewNew();
    root.innerHTML = '<div class="wrap">' + header() + tabs() + '<main>' + view + '</main></div>';
    applySorts();
  }

  /* ---------- paste parsing ---------- */
  function parseStat(s){
    s = String(s || '').trim().toLowerCase();
    if (!s) return null;
    if (s[0] === 'p') return 'P';
    if (s[0] === 'a') return 'A';
    if (s[0] === 's' || s[0] === 'r' || s[0] === 'k') return 'S';
    return null;
  }
  function parsePaste(text){
    var out = [], bad = 0;
    text.split(/\r?\n/).forEach(function(line){
      line = line.trim(); if (!line) return;
      var parts = /[;\t|]/.test(line) ? line.split(/[;\t|]/).map(function(x){ return x.trim(); }) : null;
      var p, st, ln, od, tm = '';
      if (parts && parts.length >= 4) { p = parts[0]; st = parseStat(parts[1]); ln = num(parts[2]); od = num(parts[3]); tm = parts[4] || ''; }
      else {
        var tok = line.split(/\s+/);
        if (tok.length >= 4) { od = num(tok.pop()); ln = num(tok.pop()); st = parseStat(tok.pop()); p = tok.join(' '); }
      }
      if (p && st && ln != null && od) out.push({p:p, team: tm || state.players[p] || '', stat:st, line:String(ln), odds:String(od)});
      else bad++;
    });
    return {legs:out, bad:bad};
  }

  /* ---------- events ---------- */
  document.addEventListener('click', function(ev){
    var th = ev.target.closest('table[data-sid] th[data-col]');
    if (th) {
      var tbl = th.closest('table'), sid = tbl.getAttribute('data-sid'), col = +th.getAttribute('data-col');
      ui.sorts = ui.sorts || {};
      var cur = ui.sorts[sid], dir;
      if (cur && cur.c === col) dir = -cur.d;
      else { var first = null; Array.prototype.some.call(tbl.tBodies[0].rows, function(r){ var v = cellVal(r.cells[col]); if (v != null) { first = v; return true; } return false; }); dir = typeof first === 'number' ? -1 : 1; }
      ui.sorts[sid] = {c: col, d: dir}; saveUi(); sortTable(tbl, col, dir); return;
    }
    var b = ev.target.closest('[data-act]'); if (!b || b.tagName === 'SELECT' || b.type === 'checkbox') return;
    var a = b.dataset.act, d = ui.draft;
    if (a === 'tab') { ui.tab = b.dataset.v; ui.err = ''; }
    else if (a === 'addLeg') { d.legs.push(blankLeg()); }
    else if (a === 'delLeg') { d.legs.splice(+b.dataset.i, 1); if (!d.legs.length) d.legs.push(blankLeg()); }
    else if (a === 'copyLast' || a === 'reuse') {
      var src = a === 'reuse' ? state.tickets.filter(function(t){ return t.id === b.dataset.id; })[0] : state.tickets[state.tickets.length - 1];
      if (!src) return;
      ui.draft = {date: today(), round: String(src.round), stake: String(src.stake), legs: src.legs.map(function(l){ return {p:l.p, team:l.team || '', stat:l.stat, line:String(l.line), odds:String(l.odds)}; })};
      ui.tab = 'novi'; ui.err = '';
    }
    else if (a === 'togglePaste') { ui.paste = !ui.paste; }
    else if (a === 'doPaste') {
      var box = $('#pasteBox'); var res = parsePaste(box ? box.value : '');
      if (!res.legs.length) { ui.err = 'Nijedan red nije prepoznat. Proveri format.'; }
      else {
        d.legs = d.legs.filter(function(l){ return l.p.trim() || l.line || l.odds; }).concat(res.legs);
        ui.err = res.bad ? res.bad + ' redova nije prepoznato i preskočeno je.' : '';
        ui.paste = false;
      }
    }
    else if (a === 'pickScan') { var fi = $('#scanInput'); if (fi) fi.click(); return; }
    else if (a === 'scanRetry') { ui.queue.forEach(function(q){ if (q.id === b.dataset.id) { q.status = 'waiting'; q.msg = ''; } }); saveUi(); pump(); return; }
    else if (a === 'scanDel') { ui.queue = ui.queue.filter(function(q){ return q.id !== b.dataset.id; }); delete filesMem[b.dataset.id]; saveUi(); renderScan(); return; }
    else if (a === 'scanClear') { if (running) { toast('Sačekaj da se završi čitanje.'); return; } ui.queue = []; filesMem = {}; saveUi(); renderScan(); return; }
    else if (a === 'scanSaveAll') { saveAllScanned(); return; }
    else if (a === 'scanDiag') { runDiag(); return; }
    else if (a === 'togglePasteTxt') { ui.pasteTxt = !ui.pasteTxt; saveUi(); renderScan(); return; }
    else if (a === 'readPasteTxt') {
      var tb = $('#pasteTxtBox'), txt = tb ? tb.value.trim() : '';
      if (txt.length < 10) { toast('Nalepi tekst tiketa u polje.'); return; }
      ui.queue.push({id: uid(), name: 'Nalepljen tekst', status: 'waiting', msg: '', warn: [], ticket: null, text: txt.slice(0, 40000)});
      ui.pasteTxt = false; saveUi(); renderScan(); pump(); return;
    }
    else if (a === 'scanOpen') {
      var q = ui.queue.filter(function(x){ return x.id === b.dataset.id; })[0]; if (!q) return;
      ui.draft = {date: q.ticket.date, round: d.round, stake: q.ticket.stake || d.stake, legs: clone(q.ticket.legs)};
      ui.err = q.warn.length ? 'Sa slike: ' + q.warn.join(' ') + ' Dopuni ili ispravi pa sačuvaj.' : '';
      ui.queue = ui.queue.filter(function(x){ return x.id !== q.id; }); delete filesMem[q.id];
    }
    else if (a === 'saveTicket') { saveTicket(); return; }
    else if (a === 'saveResults') { saveResults(); return; }
    else if (a === 'aSec') { ui.aSec = b.dataset.v; }
    else if (a === 'loadOffer') {
      var ob = $('#offerBox'), od = null;
      try { od = JSON.parse(ob.value.trim()); } catch(e) {}
      if (!od || !Array.isArray(od.picks) || !od.picks.length) { toast('Ponuda nije ispravna. Kopiraj je ponovo iz Admiral pomoćnika.'); return; }
      od.at = od.at || new Date().toISOString();
      try { localStorage.setItem('mt-offer', JSON.stringify(od)); } catch(e) {}
      var nso = clone(state);
      nso.offer = state.offer && String(state.offer.at) > String(od.at) ? state.offer : od;
      nso.offerSnaps = addSnap(nso.offerSnaps || [], od);
      ui.genErr = ''; ui.plan = null;
      var prevSnap = snapsOfDay(nso.offerSnaps, dayOfIso(od.at))[0];
      var dd = prevSnap && prevSnap.at !== od.at ? offerDiff(prevSnap.picks, snapPicks(od)) : null;
      save(nso, 'Ponuda učitana: ' + od.picks.length + ' linija.' + (dd ? ' Od ' + timeOfIso(prevSnap.at) + ': granica gore ' + dd.up.length + ', dole ' + dd.down.length + '.' : '')); return;
    }
    else if (a === 'linesPaste') {
      var lb = $('#linesBox'), ld = null; try { ld = JSON.parse(lb.value.trim()); } catch(e) {}
      if (!ld || !Array.isArray(ld.games)) { toast('Kvote nisu ispravne. Kopiraj ih ponovo iz pomoćnika.'); return; }
      var cls2 = clubsList(), n2 = 0; ui.linesDraft = ui.linesDraft || {};
      ld.games.forEach(function(gm){
        var hc = codeByName(gm.home, cls2), ac = codeByName(gm.away, cls2); if (!hc || !ac) return;
        var k2 = hc + '-' + ac, dd = ui.linesDraft[k2] = ui.linesDraft[k2] || {};
        ['total','hTot','aTot','ml1','ml2'].forEach(function(f){ if (gm[f] != null) dd[f] = String(gm[f]); }); n2++;
      });
      toast(n2 ? 'Ubačene kvote za ' + n2 + ' utakmica. Klikni „Sačuvaj kvote utakmica“.' : 'Utakmice nisu prepoznate.');
      var nsl0 = state.lines || {games: {}}; state.lines = {at: nsl0.at, games: Object.assign({}, nsl0.games)};
      Object.keys(ui.linesDraft).forEach(function(k3){ var cur2 = Object.assign({}, state.lines.games[k3] || {}); Object.keys(ui.linesDraft[k3]).forEach(function(f){ var v2 = num(ui.linesDraft[k3][f]); if (v2 != null) cur2[f] = v2; }); state.lines.games[k3] = cur2; });
      CTX_CACHE = null;
    }
    else if (a === 'linesSave') {
      var nsl = clone(state); nsl.lines = nsl.lines || {games: {}}; nsl.lines.games = nsl.lines.games || {};
      Object.keys(ui.linesDraft || {}).forEach(function(k3){ var cur3 = Object.assign({}, nsl.lines.games[k3] || {}); Object.keys(ui.linesDraft[k3]).forEach(function(f){ var v3 = num(ui.linesDraft[k3][f]); if (v3 != null) cur3[f] = v3; else if (String(ui.linesDraft[k3][f]).trim() === '') delete cur3[f]; }); nsl.lines.games[k3] = cur3; });
      nsl.lines.at = new Date().toISOString(); ui.linesDraft = {};
      saveUi(); save(nsl, 'Kvote utakmica su sačuvane.'); return;
    }
    else if (a === 'aiRun') { aiRun(); return; }
    else if (a === 'aiUndo') { if (ui.aiPrev) { ui.gen = ui.aiPrev; ui.aiPrev = null; ui.aiRes = null; toast('Podešavanja su vraćena.'); } }
    else if (a === 'generate') {
      if (ui.genBusy) return;
      ui.genBusy = true; render();
      setTimeout(function(){ try { ui.genErr = generatePlan(); if (!ui.genErr && ui.plan) runSim(); } catch(e) { ui.genErr = 'Greška pri generisanju: ' + (e && e.message || e); } ui.genBusy = false; saveUi(); render(); }, 40);
      return;
    }
    else if (a === 'loadCP') {
      var cp = (state.claudePlans || []).filter(function(x){ return x.id === b.dataset.v; })[0]; if (!cp) return;
      ui.plan = {at: cp.at, round: cp.round || '', warn: '', sim: null, opt: cp.stats ? cp.stats.app : null, fromClaude: cp.label, tickets: clone(cp.tickets)};
      genCfg().round = cp.round || genCfg().round; runSim(); toast('Plan „' + cp.label + '“ je učitan.');
    }
    else if (a === 'runSim') { runSim(); }
    else if (a === 'saveBudget') {
      var bv = num(($('#budgetIn') || {}).value), nsb = clone(state); nsb.settings = nsb.settings || {};
      if (bv > 0) nsb.settings.budget = bv; else delete nsb.settings.budget;
      saveUi(); save(nsb, bv > 0 ? 'Budžet je sačuvan.' : 'Budžet je uklonjen.'); return;
    }
    else if (a === 'preset') { var pr = PRESETS[b.dataset.v]; if (pr) { var gcf = genCfg(); Object.keys(pr.set).forEach(function(k){ gcf[k] = clone(pr.set[k]); }); ui.genErr = ''; toast('Primer „' + pr.label + '“ je postavljen.'); } }
    else if (a === 'addMix') { var gm = genCfg().mix, last = gm[gm.length - 1]; gm.push({legs: last ? String((parseInt(last.legs, 10) || 7) + 1) : '8', n: last ? last.n : '5'}); }
    else if (a === 'delMix') { var gm2 = genCfg().mix; gm2.splice(+b.dataset.i, 1); if (!gm2.length) gm2.push({legs: '8', n: '10'}); }
    else if (a === 'exclAll') { poolList().forEach(function(x){ genCfg().excl[x.k] = true; }); genCfg().forced = {}; }
    else if (a === 'inclAll') { genCfg().excl = {}; }
    else if (a === 'copyPlan') { copyText('planBox'); return; }
    else if (a === 'copyBm') { copyText('bmBox'); return; }
    else if (a === 'copyBmMb') { copyText('bmBoxMb'); return; }
    else if (a === 'absAdd') {
      var ai = $('#absAdd'), val = ai ? ai.value.trim() : '', C2 = ctx(); if (!val || !C2) return;
      var nm = val.replace(/\s*\([^)]*\)\s*$/, ''), kk2 = nkey(nm), found = null;
      Object.keys(C2.el.rosters || {}).forEach(function(code){ (C2.el.rosters[code] || []).forEach(function(r){ if (r[0] === kk2 || nkey(prettyName(r[2])) === kk2) found = r[0]; }); });
      if (!found) { toast('Igrač nije pronađen u sastavima. Izaberi ga sa liste.'); return; }
      var gg2 = genCfg(); gg2.absMan = gg2.absMan || {}; gg2.absMan[found] = true; if (gg2.absOff) delete gg2.absOff[found];
    }
    else if (a === 'importPlayed') {
      var pbx = $('#playedBox'), pd = null;
      try { pd = JSON.parse(pbx.value.trim()); } catch(e) {}
      if (!pd || !Array.isArray(pd.tickets) || !pd.tickets.length) { toast('Podaci nisu ispravni. Kopiraj ih ponovo iz pomoćnika.'); return; }
      var rnd = String(pd.round || genCfg().round || '').trim() || today();
      var ns3 = clone(state), sigs = savedSigs(), added = 0, dup = 0, scMap = {}, stackSet = {};
      poolList().forEach(function(x){ scMap[x.k] = Math.round(x.ev * 1000) / 1000; });
      if (ui.plan) ui.plan.tickets.forEach(function(t){ if (t.stack) stackSet[t.legs.map(function(l){ return l.c + l.s; }).sort().join(',')] = 1; });
      var overSkip = 0;
      pd.tickets.forEach(function(t){
        // plus tiketi (d: 'O') se ne upisuju: aplikacija prati samo minuse
        if ((t.legs || []).some(function(l){ return l && l.d === 'O'; })) { overSkip++; return; }
        var raw = (t.legs || []).filter(function(l){ return l && l.p && ['P','A','S'].indexOf(l.s) >= 0 && num(l.l) != null && num(l.u) > 1; });
        var legs = raw.map(function(l){ var o = {p: l.p, team: l.t || state.players[l.p] || '', stat: l.s, line: num(l.l), odds: num(l.u)}; if (scMap[l.c + l.s] != null) o.sc = scMap[l.c + l.s]; return o; });
        var isStack = !!stackSet[raw.map(function(l){ return l.c + l.s; }).sort().join(',')];
        if (!legs.length || !(num(t.stake) > 0)) return;
        if (sigs[sigOf(legs, t.stake)]) { dup++; return; }
        var nt3 = {id: uid(), date: today(), round: rnd, stake: num(t.stake), fund: genCfg().fund === 'dobitak' ? 'dobitak' : 'novi', legs: legs}; if (isStack) nt3.tag = 'stack';
        ns3.tickets.push(nt3); added++;
        legs.forEach(function(l){ if (l.team) ns3.players[l.p] = l.team; });
      });
      if (!added) { toast(overSkip ? 'Plus tiketi se ne upisuju u aplikaciju.' : dup ? 'Ovi tiketi su već upisani.' : 'Nema tiketa za upis.'); return; }
      if (ui.plan) ui.plan.saved = {at: new Date().toISOString(), round: rnd}; saveUi(); save(ns3, 'Upisano tiketa: ' + added + (dup ? ', već upisanih preskočeno: ' + dup : '') + '.'); return;
    }
    else if (a === 'savePlan') {
      if (!ui.plan) return;
      if (!confirm('Upiši ' + ui.plan.tickets.length + ' tiketa kao odigrane? Uradi ovo tek kad ih stvarno uplatiš. Ako neki tiket nisi uplatio ili se kvota promenila, posle ga ispravi ili obriši na kartici Tiketi.')) return;
      var gr = String(genCfg().round || '').trim() || today();
      var ns2 = clone(state);
      ui.plan.tickets.forEach(function(t){
        var nt = {id: uid(), date: today(), round: gr, stake: t.stake, fund: genCfg().fund === 'dobitak' ? 'dobitak' : 'novi', legs: t.legs.map(function(l){ var o = {p: l.p, team: l.t || '', stat: l.s, line: l.l, odds: l.u}; if (l.sc != null) o.sc = l.sc; return o; })};
        if (t.stack) nt.tag = 'stack';
        ns2.tickets.push(nt);
        t.legs.forEach(function(l){ if (l.t) ns2.players[l.p] = l.t; });
      });
      ui.plan.saved = {at: new Date().toISOString(), round: gr}; saveUi(); save(ns2, 'Upisano tiketa: ' + ui.plan.tickets.length + '.'); return;
    }
    else if (a === 'tFilter') { ui.tFilter = b.dataset.v; ui.tLimit = 40; }
    else if (a === 'more') { ui.tLimit += 40; }
    else if (a === 'toggleTicket') { ui.open[b.dataset.id] = !ui.open[b.dataset.id]; }
    else if (a === 'fundAll') {
      var RDf = roundDays(), ids = {};
      state.tickets.forEach(function(t){ var inf = ticketInfo(t); if (inScope(t, RDf) && (ui.tFilter === 'all' || inf.st === ui.tFilter)) ids[t.id] = 1; });
      var cnt = Object.keys(ids).length; if (!cnt) return;
      if (!confirm('Označiti ' + cnt + ' prikazanih tiketa kao ' + (b.dataset.v === 'dobitak' ? '„iz dobitka“' : '„svež novac“') + '? Za izbor tiketa koristi polje Prikaz na vrhu i filtere iznad.')) return;
      var nsa = clone(state); nsa.tickets.forEach(function(t){ if (ids[t.id]) t.fund = b.dataset.v; });
      saveUi(); save(nsa, 'Izvor novca je promenjen za ' + cnt + ' tiketa.'); return;
    }
    else if (a === 'saveRefund') {
      var rv = num(($('#ref-' + b.dataset.id) || {}).value), nsr = clone(state);
      nsr.tickets.forEach(function(t){ if (t.id === b.dataset.id) { if (rv > 0) t.refund = rv; else delete t.refund; } });
      saveUi(); save(nsr, rv > 0 ? 'Povraćaj je sačuvan.' : 'Povraćaj je uklonjen.'); return;
    }
    else if (a === 'fundToggle') {
      var nsf = clone(state); nsf.tickets.forEach(function(t){ if (t.id === b.dataset.id) t.fund = t.fund === 'dobitak' ? 'novi' : 'dobitak'; });
      saveUi(); save(nsf, 'Izvor novca je promenjen.'); return;
    }
    else if (a === 'delTicket') {
      if (!confirm('Obrisati ovaj tiket?')) return;
      var ns = clone(state); ns.tickets = ns.tickets.filter(function(t){ return t.id !== b.dataset.id; });
      saveUi(); save(ns, 'Tiket obrisan.'); return;
    }
    else if (a === 'export') { var io = $('#ioBox'); io.value = JSON.stringify(state); io.select(); return; }
    else if (a === 'import') {
      var raw = $('#ioBox').value.trim(), data;
      try { data = JSON.parse(raw); } catch(e) { toast('Podaci nisu ispravni.'); return; }
      if (!data || !Array.isArray(data.tickets)) { toast('Podaci nisu ispravni.'); return; }
      if (!confirm('Uvoz zamenjuje sve postojeće podatke. Nastaviti?')) return;
      data.results = data.results || {}; data.players = data.players || {}; data.v = 1;
      saveUi(); save(data, 'Podaci uvezeni.'); return;
    }
    saveUi(); render();
  });

  function onField(ev){
    var el = ev.target, d = ui.draft;
    if (el.dataset.g) { var gc = genCfg(); gc[el.dataset.g] = el.type === 'checkbox' ? el.checked : el.value; saveUi(); var ms2 = $('#mixSum'); if (ms2) ms2.textContent = mixSummary(gc); if (el.type === 'checkbox' && ev.type === 'change') render(); return; }
    if (el.dataset.gm) { var row = genCfg().mix[+el.dataset.i]; if (row) row[el.dataset.gm] = el.value; var ms = $('#mixSum'); if (ms) ms.textContent = mixSummary(genCfg()); saveUi(); return; }
    if (el.dataset.ln) { ui.linesDraft = ui.linesDraft || {}; var lk2 = el.dataset.ln; ui.linesDraft[lk2] = ui.linesDraft[lk2] || {}; ui.linesDraft[lk2][el.dataset.lf2] = el.value; saveUi(); return; }
    if (el.dataset.abs) { if (ev.type !== 'change') return; var gg = genCfg(); gg.absOff = gg.absOff || {}; gg.absMan = gg.absMan || {}; var kk = el.dataset.abs;
      if (el.dataset.auto === '1') { if (el.checked) delete gg.absOff[kk]; else gg.absOff[kk] = true; } else { if (el.checked) gg.absMan[kk] = true; else delete gg.absMan[kk]; }
      saveUi(); render(); return; }
    if (el.dataset.gs) { if (ev.type !== 'change') return; genCfg().stats[el.dataset.gs] = el.checked; saveUi(); render(); return; }
    if (el.dataset.gx) { if (ev.type !== 'change') return; var ex = genCfg().excl; if (el.checked) delete ex[el.dataset.gx]; else { ex[el.dataset.gx] = true; delete genCfg().forced[el.dataset.gx]; } saveUi(); render(); return; }
    if (el.dataset.gf) { if (ev.type !== 'change') return; var fo = genCfg().forced; if (el.checked) { fo[el.dataset.gf] = true; delete genCfg().excl[el.dataset.gf]; } else delete fo[el.dataset.gf]; saveUi(); render(); return; }
    if (el.id === 'scanInput') { if (ev.type === 'change') { addFiles(el.files); el.value = ''; } return; }
    if (el.dataset.f) { d[el.dataset.f] = el.value; }
    else if (el.dataset.lf) {
      var l = d.legs[+el.dataset.i]; if (!l) return;
      l[el.dataset.lf] = el.value;
      if (el.dataset.lf === 'p' && !l.team && state.players[el.value.trim()]) {
        l.team = state.players[el.value.trim()];
        var tEl = document.querySelector('[data-lf="team"][data-i="' + el.dataset.i + '"]'); if (tEl) tEl.value = l.team;
      }
    }
    else if (el.dataset.rf) {
      var k = el.dataset.k, e = picks(true).filter(function(x){ return x.k === k; })[0]; if (!e) return;
      var v = ui.resDraft[k] || resValue(e);
      v = Object.assign({}, v);
      v[el.dataset.rf] = el.type === 'checkbox' ? el.checked : el.value;
      ui.resDraft[k] = v;
      var row = el.closest('tr'), badge = row && row.querySelector('[data-badge]');
      if (badge) { var s = draftStatus(v, e.line); badge.className = 'tag ' + s; badge.textContent = STATUS_TXT[s]; }
    }
    else if (el.dataset.act === 'scope' && ev.type === 'change') { ui.scope = el.value; saveUi(); render(); return; }
    else if (el.dataset.act === 'tSort' && ev.type === 'change') { ui.tSort = el.value; saveUi(); render(); return; }
    else if (el.dataset.act === 'resRound' && ev.type === 'change') { ui.resRound = el.value; saveUi(); render(); return; }
    else if (el.dataset.act === 'toggleSettled' && ev.type === 'change') { ui.showSettled = el.checked; saveUi(); render(); return; }
    else return;
    var c = $('#calc'); if (c && (el.dataset.f || el.dataset.lf)) c.innerHTML = draftCalc();
    saveUi();
  }
  document.addEventListener('input', onField);
  document.addEventListener('change', onField);

  function saveTicket(){
    var d = ui.draft, err = '', legs = [];
    var round = String(d.round).trim(), stake = num(d.stake);
    for (var i = 0; i < d.legs.length; i++) {
      var l = d.legs[i];
      if (!l.p.trim() && !String(l.line).trim() && !String(l.odds).trim()) continue;
      var line = num(l.line), odds = num(l.odds);
      if (!l.p.trim() || line == null || odds == null || odds <= 1) { err = 'Par ' + (i + 1) + ': treba igrač, linija i kvota veća od 1.'; break; }
      legs.push({p: l.p.trim(), team: l.team.trim(), stat: l.stat, line: line, odds: odds});
    }
    if (!err && !legs.length) err = 'Dodaj bar jedan par.';
    if (!err && !round) err = 'Upiši kolo.';
    if (!err && (stake == null || stake <= 0)) err = 'Upiši ulog.';
    if (err) { ui.err = err; render(); return; }
    ui.err = '';
    var ns = clone(state);
    ns.tickets.push({id: uid(), date: d.date || today(), round: round, stake: stake, fund: d.fund === 'dobitak' ? 'dobitak' : 'novi', legs: legs});
    legs.forEach(function(l){ if (l.team) ns.players[l.p] = l.team; else if (!(l.p in ns.players)) ns.players[l.p] = ''; });
    save(ns, 'Tiket sačuvan.', function(){ ui.draft = blankDraft(); });
  }
  function saveResults(){
    var keys = Object.keys(ui.resDraft);
    if (!keys.length) { toast('Nema novih rezultata za čuvanje.'); return; }
    var ns = clone(state);
    keys.forEach(function(k){
      var v = ui.resDraft[k], a = num(v.actual), old = ns.results[k] || {};
      var oc = a == null && !v.dnp ? (v.outcome || '') : '';
      if (a == null && !v.dnp && !oc) { delete ns.results[k]; return; }
      ns.results[k] = {actual: a, dnp: !!v.dnp};
      if (old.min && a != null && a === old.actual) ns.results[k].min = old.min;
      if (oc) ns.results[k].outcome = oc;
    });
    save(ns, 'Rezultati sačuvani.', function(){ ui.resDraft = {}; });
  }

  render();
  if (flash) toast(flash);
})();
