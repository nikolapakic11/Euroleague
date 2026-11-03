! function() {
    if (window.__mbPanel) window.__mbPanel.style.display = "block";
    else {
        var e = "mt-maxbet-plan",
            t = {
                P: "poeni",
                A: "asist.",
                S: "skokovi"
            },
            a = {
                P: ["ouPlPoints", "51681", "51679"],
                A: ["ouPlAssists", "51684", "51682"],
                S: ["ouPlRebounds", "51687", "51685"]
            },
            n = "https://feeds.incrowdsports.com/provider/euroleague-feeds/v3/competitions/E/statistics/",
            i = "https://api-live.euroleague.net/v2/competitions/E/seasons/",
            o = ["nedelja", "ponedeljak", "utorak", "sreda", "četvrtak", "petak", "subota"],
            r = function() {
                try {
                    return JSON.parse(localStorage.getItem(e) || "null")
                } catch (e) {
                    return null
                }
            }(),
            s = [],
            l = document.createElement("div");
        window.__mbPanel = l, l.style.cssText = "position:fixed;left:12px;bottom:12px;width:340px;max-height:80vh;overflow:auto;z-index:2147483647;background:#fff;color:#15223a;border:2px solid #1f6feb;border-radius:8px;box-shadow:0 6px 24px rgba(0,0,0,.35);font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;padding:12px", document.body.appendChild(l), l.addEventListener("click", async function(e) {
            var t = e.target.closest("[data-a]");
            if (t) {
                var f = t.getAttribute("data-a");
                if ("build" === f) return void BUILD();
                if ("unbuild" === f) { var ub = r.tickets[r.idx || 0]; ub && (ub.built = !1, ub.actual = null, ub.marks = {}); g(); s = []; return void y(); }
                if ("close" !== f)
                    if ("showplan" !== f)
                        if ("loadplan" !== f) {
                            if ("next" === f || "prev" === f) return r.idx = Math.max(0, Math.min((r.idx || 0) + ("next" === f ? 1 : -1), r.tickets.length)), g(), s = [], void y();
                            if ("played" === f) {
                                var v = r.tickets[r.idx || 0];
                                return v && (v.done = !0, r.idx = Math.min((r.idx || 0) + 1, r.tickets.length), g(), s = ["Tiket označen kao odigran."]), void y()
                            }
                            if ("copyplayed" !== f) {
                                if ("offer" === f) {
                                    var x;
                                    s = ["Preuzimam ponudu sa MaxBeta…"], y();
                                    try {
                                        x = await async function() {
                                            var e = location.origin + "/restapi/offer/sr/",
                                                t = null;
                                            try {
                                                ((await m(e + "categories/sport/SK/l?annex=3&locale=sr", !0)).categories || []).forEach(function(e) {
                                                    !t && /poeni igra.a euroleague/i.test(e.name || "") && (t = e.id)
                                                })
                                            } catch (e) {}
                                            t || (t = "194042");
                                            var n = await m(e + "sport/SK/league/" + t + "/mob?annex=3&locale=sr", !0),
                                                i = [];
                                            return (n.esMatches || []).forEach(function(e) {
                                                if (!e.blocked && !e.live) {
                                                    var t = e.odds || {},
                                                        n = e.params || {};
                                                    Object.keys(a).forEach(function(r) {
                                                        var s, l, c = a[r],
                                                            p = d(n[c[0]]),
                                                            f = d(t[c[1]]),
                                                            m = d(t[c[2]]);
                                                        null != p && f && i.push({
                                                            c: String(e.matchCode),
                                                            p: e.home,
                                                            t: e.away,
                                                            s: r,
                                                            l: p,
                                                            u: f,
                                                            o: m,
                                                            time: (s = e.kickOffTime, l = new Date(s), o[l.getDay()] + ", " + u(l.getDate()) + ". " + u(l.getMonth() + 1) + ". " + l.getFullYear() + ". " + u(l.getHours()) + ":" + u(l.getMinutes())),
                                                            id: e.id
                                                        })
                                                    })
                                                }
                                            }), i
                                        }()
                                    } catch (e) {
                                        return s = ["Ponuda nije preuzeta: " + (e.message || e) + ". Otvori MaxBet stranicu i pokušaj ponovo."], void y()
                                    }
                                    if (!x.length) return s = ["U ponudi Poeni igrača EUROLEAGUE trenutno nema igrača."], void y();
                                    s = ["Ponuda: " + x.length + " linija. Preuzimam statistiku sa Evrolige…"], y();
                                    var k = {};
                                    x.forEach(function(e) {
                                        k[e.t] = 1
                                    });
                                    var j = null,
                                        S = "";
                                    try {
                                        j = await async function(e) {
                                            var t = new Date,
                                                a = t.getMonth() >= 6 ? t.getFullYear() : t.getFullYear() - 1,
                                                o = "E" + a,
                                                r = "E" + (a - 1),
                                                s = function(e) {
                                                    return m(e + "&phaseTypeCode=RS").then(function(t) {
                                                        return t.players && t.players.length || t.teams && t.teams.length ? t : m(e)
                                                    }, function() {
                                                        return m(e)
                                                    })
                                                },
                                                l = function() {
                                                    return {
                                                        teams: []
                                                    }
                                                },
                                                d = await Promise.all([s(n + "players/traditional?seasonMode=Single&limit=3000&statisticMode=perGame&seasonCode=" + o), m(i + o + "/games"), s(n + "teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=" + o).catch(l), m(n + "teams/opponentsTraditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=" + r).catch(l), s(n + "teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=" + o).catch(l), m(n + "teams/traditional?seasonMode=Single&statisticMode=perGame&limit=60&seasonCode=" + r).catch(l)]),
                                                u = {
                                                    season: o,
                                                    at: t.toISOString(),
                                                    players: {},
                                                    games: [],
                                                    clubs: {},
                                                    def: {
                                                        cur: {},
                                                        prev: {}
                                                    },
                                                    rosters: {},
                                                    tmap: {}
                                                };
                                            (d[0].players || []).forEach(function(e) {
                                                var t = e.gamesPlayed || 0;
                                                t && (u.players[p(e.player.name)] = [t, Math.round(10 * e.minutesPlayed) / 10, e.pointsScored, e.totalRebounds, e.assists, String(e.player.team && e.player.team.code || "").split(";").pop(), e.foulsCommited || 0], u.perGame = !0)
                                            });
                                            var f = function(e) {
                                                return e.twoPointersAttempted + e.threePointersAttempted + .44 * e.freeThrowsAttempted - e.offensiveRebounds + e.turnovers
                                            };
                                            [
                                                ["cur", d[2], d[4]],
                                                ["prev", d[3], d[5]]
                                            ].forEach(function(e) {
                                                var t = {};
                                                (e[2].teams || []).forEach(function(e) {
                                                    t[e.team.code] = f(e)
                                                }), (e[1].teams || []).forEach(function(a) {
                                                    var n = f(a),
                                                        i = t[a.team.code] || n;
                                                    u.def[e[0]][a.team.code] = [a.gamesPlayed, a.pointsScored, a.totalRebounds, a.assists, Math.round((n + i) / 2 * 10) / 10, Math.round(a.pointsScored / n * 1e3) / 10]
                                                })
                                            });
                                            var g = t.getTime() - 432e5,
                                                h = t.getTime() + 3456e5;
                                            return (d[1].data || []).forEach(function(e) {
                                                var t = Date.parse(e.utcDate || e.date);
                                                t >= g && t <= h && !e.played && ([e.local.club, e.road.club].forEach(function(e) {
                                                    u.clubs[e.code] = {
                                                        name: e.name,
                                                        abbr: e.abbreviatedName || "",
                                                        ed: e.editorialName || ""
                                                    }
                                                }), u.games.push({
                                                    d: e.utcDate || e.date,
                                                    h: e.local.club.code,
                                                    a: e.road.club.code
                                                }))
                                            }), e.forEach(function(e) {
                                                var t = c(e).split(" "),
                                                    a = null,
                                                    n = 0;
                                                Object.keys(u.clubs).forEach(function(e) {
                                                    var i = u.clubs[e],
                                                        o = c(i.name + " " + i.abbr + " " + i.ed).split(" "),
                                                        r = 0;
                                                    t.forEach(function(e) {
                                                        e.length > 2 && o.indexOf(e) >= 0 && (r += e.length)
                                                    }), r > n && (n = r, a = e)
                                                }), a && (u.tmap[e] = a)
                                            }), await Promise.all(Object.keys(u.clubs).map(function(e) {
                                                return m(i + o + "/clubs/" + e + "/people").then(function(t) {
                                                    u.rosters[e] = (t || []).filter(function(e) {
                                                        return "J" === e.type && !1 !== e.active && e.person
                                                    }).map(function(e) {
                                                        return [p(e.person.name), e.positionName || "", e.person.name]
                                                    })
                                                }).catch(function() {})
                                            })), u
                                        }(Object.keys(k))
                                    } catch (e) {
                                        S = e.message || "greška"
                                    }
                                    P = JSON.stringify({
                                        v: 2,
                                        src: "maxbet",
                                        at: (new Date).toISOString(),
                                        picks: x,
                                        el: j
                                    });
                                    var w = j ? "Statistika: " + Object.keys(j.players).length + " igrača, " + j.games.length + " utakmica." : "Statistika nije preuzeta (" + S + "), kopirana je samo ponuda.";
                                    h(P).then(function(e) {
                                        s = [w, e ? "Ponuda kopirana (" + x.length + " linija). Nalepi je u aplikaciju, Generator." : "Kopiranje nije uspelo, kopiraj tekst ispod ručno."], y(), e || b(P)
                                    })
                                }
                            } else {
                                var P, E = r.tickets.filter(function(e) {
                                    return e.done
                                }).map(function(e) {
                                    return {
                                        stake: e.stake,
                                        legs: (e.built && e.actual && e.actual.length ? e.actual : e.legs).map(function(e) {
                                            return {
                                                c: e.c,
                                                p: e.p,
                                                t: e.t || "",
                                                s: e.s,
                                                l: e.l,
                                                u: e.u
                                            }
                                        })
                                    }
                                });
                                h(P = JSON.stringify({
                                    v: 1,
                                    kind: "played",
                                    round: r.round || "",
                                    at: (new Date).toISOString(),
                                    tickets: E
                                })).then(function(e) {
                                    s = [e ? "Kopirano " + E.length + " odigranih tiketa." : "Kopiranje nije uspelo, kopiraj tekst ispod ručno."], y(), e || b(P)
                                })
                            }
                        } else {
                            try {
                                var M = JSON.parse(l.querySelector("#mb-plan").value.trim());
                                if (!M || !Array.isArray(M.tickets) || !M.tickets.length) throw 0;
                                M.idx = 0, r = M, g(), s = ["Plan učitan: " + M.tickets.length + " tiketa."]
                            } catch (e) {
                                s = ["Plan nije ispravan. Kopiraj ga ponovo iz aplikacije."]
                            }
                            y()
                        }
                else {
                    var O = l.querySelector("#mb-planbox");
                    O.style.display = "none" === O.style.display ? "block" : "none"
                } else l.style.display = "none"
            }
        }), y()
    }

    function c(e) {
        var t = String(e || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/đ/g, "dj");
        return (t = t.replace(/\b([a-z])\.\s*([a-z])\./g, "$1$2").replace(/[-.]/g, " ").replace(/[^a-z ]/g, "")).split(/\s+/).filter(function(e) {
            return e && ["jr", "sr", "ii", "iii", "iv"].indexOf(e) < 0
        }).join(" ")
    }

    function p(e) {
        if (e.indexOf(",") >= 0) {
            var t = e.split(",");
            return c(t[1] + " " + t[0])
        }
        return c(e)
    }

    function d(e) {
        var t = parseFloat(String(null == e ? "" : e).replace(",", "."));
        return isFinite(t) ? t : null
    }

    function u(e) {
        return (e < 10 ? "0" : "") + e
    }

    function f(e) {
        return String(null == e ? "" : e).replace(/[&<>"]/g, function(e) {
            return {
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;"
            } [e]
        })
    }
    async function m(e, t) {
        var a = await fetch(e, {
            credentials: t ? "include" : "omit"
        });
        if (!a.ok) throw new Error("HTTP " + a.status);
        return a.json()
    }

    function g() {
        try {
            localStorage.setItem(e, JSON.stringify(r))
        } catch (e) {}
    }

    function h(e) {
        function t() {
            var t = document.createElement("textarea");
            t.value = e, t.style.cssText = "position:fixed;left:-9999px", document.body.appendChild(t), t.select();
            var a = !1;
            try {
                a = document.execCommand("copy")
            } catch (e) {}
            return t.remove(), a
        }
        return navigator.clipboard && navigator.clipboard.writeText ? navigator.clipboard.writeText(e).then(function() {
            return !0
        }, function() {
            return t()
        }) : Promise.resolve(t())
    }

    function v(e, t, a) {
        return '<button data-a="' + t + '" style="margin:3px 4px 3px 0;padding:6px 10px;border-radius:4px;cursor:pointer;font:inherit;font-weight:600;border:1px solid ' + (a ? "#1f6feb;background:#1f6feb;color:#fff" : "#b8c0cc;background:#f4f6f9;color:#15223a") + '">' + e + "</button>"
    }

    function y() {
        var e = '<div style="display:flex;justify-content:space-between;align-items:center"><b style="font-size:15px">MaxBet pomoćnik</b>' + v("×", "close") + "</div>";
        if (e += "<div>" + v("Kopiraj ponudu i statistiku", "offer", !0) + v("Nalepi plan", "showplan") + "</div>", e += '<div id="mb-planbox" style="display:none"><textarea id="mb-plan" style="width:100%;height:80px;font:11px monospace" placeholder="Nalepi plan iz aplikacije"></textarea>' + v("Učitaj plan", "loadplan", !0) + "</div>", r && r.tickets && r.tickets.length) {
            var a = r.idx || 0,
                n = r.tickets[a];
            e += '<div style="margin-top:8px;padding-top:8px;border-top:1px solid #ddd">Plan: <b>' + r.tickets.length + " tiketa</b>" + (r.round ? ", kolo " + f(r.round) : "") + "</div>", n ? (e += '<div style="margin:6px 0"><b>Tiket ' + (a + 1) + " od " + r.tickets.length + "</b>, ulog " + f(n.stake) + " din, " + n.legs.length + " parova</div>", e += '<ol style="margin:0 0 6px;padding-left:20px">' + n.legs.map(function(e) {
                var mk = (n.marks || {})[e.c + e.s];
                return "<li>" + (mk ? '<span style="color:' + (mk.ok ? "#1d7a4b" : "#b2261e") + '">' + (mk.ok ? "✓ " : "✗ ") + "</span>" : "") + "<b>" + f(e.c) + "</b> " + f(e.p) + ", " + t[e.s] + " manje " + e.l + " @ " + e.u + (mk && mk.msg ? ' <i style="color:' + (mk.ok ? "#8a6d00" : "#b2261e") + '">' + f(mk.msg) + "</i>" : "") + "</li>"
            }).join("") + "</ol>", e += '<div style="display:flex;gap:6px">' + v("‹ Prethodni", "prev") + v("Sledeći ›", "next") + "</div>", e += "<div>" + v(BUSY ? "Slažem…" : "Složi tiket " + (a + 1), "build", !0) + (n.built ? v("Odigran ✓", "played", !0) + v("Nisam uplatio", "unbuild") : v("Odigran ✓", "played")) + "</div>") : e += "<p><b>Svi tiketi iz plana su prošli.</b></p>";
            var i = r.tickets.filter(function(e) {
                return e.done
            }).length;
            i && (e += "<div>" + v("Kopiraj odigrano (" + i + ")", "copyplayed") + "</div>")
        } else e += '<p style="color:#5a6678">Nema učitanog plana.</p>';
        s.length && (e += '<div style="margin-top:6px;padding:6px;background:#f4f6f9;border-radius:4px">' + s.map(f).join("<br>") + "</div>"), e += '<p style="color:#5a6678;font-size:12px;margin:8px 0 0">Pomoćnik dodaje parove i upisuje ulog. Tiket proveri i uplati ti, dugmetom UPLATI, pa klikni Odigran.</p>', l.innerHTML = e
    }

    function b(e) {
        var t = document.createElement("textarea");
        t.value = e, t.style.cssText = "width:100%;height:80px;font:11px monospace", l.appendChild(t), t.select()
    }

    var BUSY = !1;
    function SLP(e) { return new Promise(function(t) { setTimeout(t, e) }) }
    async function WF(e, t) { for (var a = Date.now(); Date.now() - a < (t || 8e3);) { var n = e(); if (n) return n; await SLP(150) } return null }
    function VIS(e) { return !!(e && null !== e.offsetParent) }
    function NUM(e) { var t = String(e || "").replace(/[()\s]/g, "").replace(",", "."); var a = parseFloat(t); return isFinite(a) ? a : null }
    function TXT(e) { return String(e && e.textContent || "").replace(/ /g, " ").replace(/\s+/g, " ").trim() }
    function SLIPN() { return document.querySelectorAll("ds-content-ticket ds-ticket-match").length }
    function ONSLIP(e) { return document.getElementById(e + "-ticket") }
    function SPEC() { var e = [].slice.call(document.querySelectorAll("ds-match-special")).filter(VIS); return e.length ? e[e.length - 1] : null }
    function ROW(e) { for (var t = document.querySelectorAll("ion-grid.es-match"), a = 0; a < t.length; a++) { var n = t[a].querySelectorAll(".es-match-teams-item"); if (n.length && c(n[0].textContent) === c(e)) return t[a] } return null }
    async function GOLIST() { var e = SPEC(); if (!e) return !0; var t = e.querySelector("ion-button.back-button, .match-special--bck-btn"); t ? t.click() : history.back(); return !!await WF(function() { return !SPEC() && VIS(document.querySelector("ion-grid.es-match")) }, 7e3) }
    var GN = { P: "poeni igraca", S: "skokovi igraca", A: "asistencije igraca" }, TIP = { P: "-", S: "SK-", A: "AS-" }, SW = { P: "poeni", S: "skokovi", A: "asistencije" };
    async function EMPTY() {
        if (!SLIPN()) return !0;
        var e = document.querySelector("ion-button.ticket--empty-btn"); if (!e) return !1;
        e.click(); await SLP(600);
        var t = document.querySelector("ion-alert"); if (t && SLIPN()) { var a = t.querySelectorAll("button"); a.length && a[a.length - 1].click(); await SLP(600) }
        return !!await WF(function() { return !SLIPN() }, 3e3)
    }
    async function ADD(e, n) {
        var k = e.c + e.s, mk = { ok: !1, msg: "" }, btn = null, line = null;
        if (ONSLIP(e.c)) return { ok: !1, msg: "igrač je već na tiketu" };
        if ("P" === e.s) {
            if (SPEC() && !await GOLIST()) return { ok: !1, msg: "povratak na listu nije uspeo" };
            var row = ROW(e.p); if (!row) return { ok: !1, msg: "nije u ponudi" };
            var bs = row.querySelectorAll("button.odd-btn");
            for (var i = 0; i < bs.length; i++) { var ti = bs[i].getAttribute("title") || ""; if (/manje poena/i.test(ti) && !/alternat/i.test(ti)) { btn = bs[i]; break } }
            if (!btn) return { ok: !1, msg: "dugme za manje nije nađeno" };
            line = NUM(TXT(btn.querySelector(".odd-btn--special-value")))
        } else {
            var sp = SPEC();
            if (!sp || TXT(sp.querySelector(".match-special-teams")).toLowerCase().indexOf(String(e.p).toLowerCase()) < 0) {
                if (sp && !await GOLIST()) return { ok: !1, msg: "povratak na listu nije uspeo" };
                var rw = ROW(e.p); if (!rw) return { ok: !1, msg: "nije u ponudi" };
                var it = rw.querySelector(".es-match-teams-item"); it.click();
                sp = await WF(function() { var x = SPEC(); return x && TXT(x.querySelector(".match-special-teams")).toLowerCase().indexOf(String(e.p).toLowerCase()) >= 0 && x.querySelector("ds-match-special-group") ? x : null }, 9e3);
                if (!sp) return { ok: !1, msg: "stranica igrača se nije otvorila" }
            }
            var grp = await WF(function() {
                for (var x = sp.querySelectorAll("ds-match-special-group"), y = 0; y < x.length; y++) {
                    var h = x[y].querySelector(".match-special-bet-pick-group"), b = h && h.querySelector("b"), nm = c(TXT(h).replace(TXT(b), ""));
                    if (nm === GN[e.s]) return x[y]
                } return null
            }, 6e3);
            if (!grp) return { ok: !1, msg: "kod igrača nema " + SW[e.s] };
            line = NUM(TXT(grp.querySelector(".match-special-bet-pick-group b")));
            for (var q = grp.querySelectorAll("button.odd-btn"), z = 0; z < q.length; z++) if (TXT(q[z].querySelector(".odd-btn--tip")) === TIP[e.s]) { btn = q[z]; break }
            if (!btn) return { ok: !1, msg: "dugme za manje nije nađeno" }
        }
        var odd = NUM(TXT(btn.querySelector(".odd-btn--odd")));
        if (null == line) return { ok: !1, msg: "granica nije pročitana, dodaj ručno" };
        if (line < e.l) return { ok: !1, msg: "granica spuštena na " + line + ", nije dodato" };
        btn.click();
        var on = await WF(function() { return ONSLIP(e.c) }, 4e3);
        if (!on) return { ok: !1, msg: "klik nije prošao" };
        var gtx = c(TXT(on.querySelector(".ticket-match--group-name")));
        if (gtx && gtx.indexOf(SW[e.s]) < 0) return { ok: !1, msg: "na tiketu je druga igra (" + TXT(on.querySelector(".ticket-match--group-name")) + "), proveri" };
        var w = [];
        line > e.l && w.push("granica podignuta na " + line);
        odd && odd !== e.u && w.push("kvota " + odd);
        n.push({ c: e.c, p: e.p, t: e.t || "", s: e.s, l: line, u: odd || e.u });
        return { ok: !0, msg: w.join(", ") }
    }
    function STAKE(e) {
        var t = document.querySelector("ion-input.ticket-payin-input-field input") || document.querySelector(".ticket-payin-input input");
        if (!t) return !1;
        var a = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, "value");
        t.focus(); a && a.set ? a.set.call(t, String(e)) : t.value = String(e);
        ["input", "change", "keyup"].forEach(function(e) { t.dispatchEvent(new Event(e, { bubbles: !0 })) });
        t.blur(); t.dispatchEvent(new Event("blur", { bubbles: !0 }));
        return !0
    }
    async function BUILD() {
        if (BUSY || !r || !r.tickets) return;
        var e = r.tickets[r.idx || 0]; if (!e) return;
        BUSY = !0; s = []; e.marks = {}; y();
        try {
            if (!document.querySelector("ion-grid.es-match")) throw new Error("Otvori ponudu Poeni igrača EUROLEAGUE (lista igrača), pa klikni ponovo.");
            if (!await EMPTY()) throw new Error("Tiket nije prazan. Obriši ga ručno (kanta na tiketu) pa klikni ponovo.");
            var legs = e.legs.slice().sort(function(a, b) { return ("P" === a.s ? 0 : 1) - ("P" === b.s ? 0 : 1) }), act = [], ok = 0;
            for (var i = 0; i < legs.length; i++) {
                var L = legs[i], res;
                try { res = await ADD(L, act) } catch (x) { res = { ok: !1, msg: "greška: " + (x.message || x) } }
                e.marks[L.c + L.s] = res; res.ok && ok++; y(); await SLP(250)
            }
            await GOLIST(); await SLP(400);
            e.actual = act; e.built = ok > 0;
            var st = STAKE(e.stake);
            s.unshift("Dodato " + ok + " od " + e.legs.length + " parova. Na tiketu: " + SLIPN() + ".");
            s.push(st ? "Ulog " + e.stake + " din je upisan. Proveri iznos na tiketu." : "Polje za ulog nije pronađeno, upiši ulog ručno.");
            ok < e.legs.length && s.push("Neki parovi nisu dodati (označeni crveno). Možeš ih dodati ručno ili igrati tiket bez njih.");
            s.push("Proveri tiket i klikni UPLATI, pa ovde Odigran ✓.");
            var up = [].slice.call(document.querySelectorAll("ds-navbar-bottom-ticket button, ds-navbar-bottom-ticket ion-button")).filter(function(x) { return /UPLATI/i.test(x.textContent || "") })[0];
            if (up) { up.style.outline = "3px solid #1f6feb"; up.style.outlineOffset = "2px"; try { up.scrollIntoView({ block: "center", behavior: "smooth" }) } catch (x) {} }
        } catch (x) { s.push(x.message || String(x)) }
        BUSY = !1; g(); y()
    }
}();