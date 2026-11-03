import re
js=open('app.orig.js').read()
def rep(old,new,cnt=1):
    global js
    assert js.count(old)==cnt,(js.count(old),old[:80])
    js=js.replace(old,new)
# 1) konstante i funkcija za kontekst
rep("""  var EST = {c: 0.16, kf: 0.5, A: 0.12, S: 0.08, P10: 0.12};""",
"""  var EST = {c: 0.16, kf: 0.5, A: 0.12, S: 0.08, P10: 0.12};
  // v6 (24.10.2026, 1.124 minusa iz cele ponude, 8 dana): kontekst utakmice. Protivnik koji dobro brani igračevu poziciju i spor meč (malo očekivanih poena tima)
  // podižu šansu; tesan meč (razlika do 5 poena) podiže; vruća forma (učinak po minutu u poslednje 3 iznad 130% sezone) i rezervista autsajdera obaraju.
  // Na najboljoj četvrtini ponude prolaz je porastao sa 62% na 69% i bio bolji u 6 od 8 dana. Koeficijenti su namerno umereni (mali uzorak).
  var ADJ = {of: 1.5, pace: 1.5, close: 0.2, hot: 0.15, dogB: 0.1};
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
    r.dz = (r.of != null ? -ADJ.of * (r.of - 1) : 0) + (r.pace != null ? -ADJ.pace * (r.pace - 1) : 0) + (r.close ? ADJ.close : 0) - (r.hot ? ADJ.hot : 0) - (r.dogB ? ADJ.dogB : 0);
    return r;
  }""")
# 2) estimate: kontekst u z, očekivano bez dvostrukog računanja
rep("""    if (b > 1.02) z -= (mpM != null && mpM >= 25 ? 1.2 : 2.5) * (b - 1);""",
"""    if (b > 1.02) z -= (mpM != null && mpM >= 25 ? 1.2 : 2.5) * (b - 1);
    var adj = ctx2Adj(pk, X); if (adj) z += adj.dz;
    // ritam i odbrana su sada u kontekstu, pa se za ovaj deo koristi prosek bez njih (da se ne računaju dvaput)
    var mpR = adj && A && A.v != null ? modelUnder(pk.s, pk.l, A.v * b) : mp;""")
rep("""    if (mp != null && nEff > 0) z += 0.25 * nEff / (nEff + 20) * (lgt(mp) - lgt(fair));""",
"""    if (mpR != null && nEff > 0) z += 0.25 * nEff / (nEff + 20) * (lgt(mpR) - lgt(fair));""")
rep("""cx: X, out: X ? X.out : false, ms: ms, mpM: mpM, role: roleOf(mpM)};""",
"""cx: X, out: X ? X.out : false, ms: ms, mpM: mpM, role: roleOf(mpM), adj: adj};""")
# 3) prikaz u koloni Uloga
rep("""    var tag = x.cls === 'A' ? '<span class="tag dobro">više tiketa</span>'""",
"""    var a = x.adj, kb = [];
    if (a) {
      var PN = {G: 'bekove', F: 'krila', C: 'centre'}, SN = {P: 'poene', S: 'skokove', A: 'asistencije'};
      if (a.of != null && Math.abs(a.of - 1) >= 0.04) kb.push((a.of < 1 ? 'protivnik dobro brani ' : 'protivnik slabo brani ') + (PN[a.pos] || 'tu poziciju') + ' za ' + SN[x.s] + ' (' + (a.of > 1 ? '+' : '−') + Math.round(Math.abs(a.of - 1) * 100) + '%)');
      if (a.pace != null && a.pace >= 1.04) kb.push('brz meč, tim očekuje mnogo poena');
      else if (a.pace != null && a.pace <= 0.96) kb.push('spor meč, tim očekuje malo poena');
      if (a.close) kb.push('tesan meč');
      else if (a.spread != null) kb.push(a.spread > 0 ? 'favorit (+' + Math.round(a.spread) + ')' : 'autsajder (' + Math.round(a.spread) + ')');
      if (a.hot) kb.push('vruća forma u poslednje 3 utakmice');
      if (a.dogB) kb.push('rezervista autsajdera, više minuta ako se meč reši');
    }
    var tag = x.cls === 'A' ? '<span class="tag dobro">više tiketa</span>'""")
rep("""    return tag + '<br><small style="color:var(--muted)">' + esc(bits.join(', ')) + '</small>';""",
"""    return tag + '<br><small style="color:var(--muted)">' + esc(bits.join(', ')) + '</small>' + (kb.length ? '<br><small class="' + (a.dz > 0.02 ? 'pos' : a.dz < -0.02 ? 'neg' : '') + '" title="Kontekst utakmice: ' + (a.dz > 0 ? '+' : '') + fmt(a.dz * 100 / 4, 1) + ' procentnih poena šanse">' + esc('Kontekst: ' + kb.join(', ')) + '</small>' : '');""")
# 4) objašnjenje
rep("""Tvoji dosadašnji rezultati po igraču se više ne računaju, jer posle sedam kola nisu ništa predviđali.""",
"""Od 24.10. računa se i kontekst utakmice: protivnik koji dobro brani igračevu poziciju (bekove, krila ili centre) i spor meč sa malo očekivanih poena tima (iz kvota utakmica, a bez njih iz proseka timova) podižu šansu; tesan meč (razlika do 5 poena) podiže; vruća forma u poslednje 3 utakmice i rezervista ekipe koja je autsajder obaraju. Sve to piše u koloni Uloga, u redu „Kontekst“. Tvoji dosadašnji rezultati po igraču se više ne računaju, jer posle sedam kola nisu ništa predviđali.""")
open('app.js','w').write(js)
print('ok',len(js))
