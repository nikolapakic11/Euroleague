import re,json,time
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
cur=open('app.js').read(); assert h.count(cur)==1
js=cur
def rep(old,new):
    global js
    assert js.count(old)==1,old[:70]; js=js.replace(old,new)
rep("""      var nR = rounds().length;
      var reminder = '<section class="advice" style="border-left-color:' + (nR >= 3 ? 'var(--accent)' : 'var(--line)') + '"><p><b>' + (nR >= 3 ? 'Vreme je za proveru.' : 'Sledeća provera: posle 3. kola.') + '</b> ' + (nR >= 3 ? 'Imaš podatke iz ' + nR + ' kola.""",
"""      var nR = rounds().length, RV = state.review, due = RV && RV.n ? nR >= RV.n + 3 : nR >= 3;
      var reminder = RV && RV.n && !due ? '<section class="advice" style="border-left-color:var(--line)"><p><b>Poslednja provera: ' + esc(RV.at) + ', posle ' + RV.n + '. kola.</b> ' + esc(RV.sum || '') + ' Sledeća provera posle ' + (RV.n + 3) + '. kola.</p></section>' : '<section class="advice" style="border-left-color:' + (due ? 'var(--accent)' : 'var(--line)') + '"><p><b>' + (due ? 'Vreme je za proveru.' : 'Sledeća provera: posle 3. kola.') + '</b> ' + (due ? 'Imaš podatke iz ' + nR + ' kola.""")
rep("""    if (!g.v5) { g.v5 = true; g.best = false; }""",
"""    if (!g.v5) { g.v5 = true; g.best = false; }
    // provera posle 7. kola: parovi sa najviše ponavljanja prolazili su lošije od ostalih, pa ★ ne dobija dodatna ponavljanja dok nova procena ne potvrdi da ih zaslužuje
    if (!g.v6) { g.v6 = true; g.strong = false; }""")
rep(""">Najbolja vrednost (šansa u odnosu na kvotu)</option>""",
""">Najbolja vrednost (šansa u odnosu na kvotu; ne preporučuje se, u proveri posle 7. kola nije razlikovala dobre i loše parove)</option>""")
open('app.review.js','w').write(js)
h=h.replace(cur,js)
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
st['review']={'at':'24.10.2026','n':7,'sum':('Tvoji odigrani parovi prolazili su kao cela ponuda (57,6% prema 57,1%), a najviše ponavljani parovi lošije od ostalih (52% prema 59%). '
  'Stara „Šansa“ nije razlikovala parove bolje od samih kvota, a „Vrednost“ nije razlikovala uopšte. Nova procena sa kontekstom utakmice (od 24.10.) u proveri van uzorka podigla je najbolju četvrtinu sa 55% na 65%. '
  'Minusi iz iste utakmice ne zavise jedan od drugog, pa tiketi oko jedne utakmice ne prolaze češće. Igrači sa 12 do 17 minuta: skokovi i asistencije dobri (64 do 67%), poeni slabi (52%); najveći rizik je skok minutaže. '
  'Osmice ostaju osnova; desetke imaju nešto veći očekivani dobitak, ali ređe dobitne dane i najveće gubitke kad prolaz parova padne. ★ više ne dobija dodatna ponavljanja.')}
notes=st['notes']['text']
N=("Provera posle 7. kola (24.10.2026): (1) cela ponuda minusa prolazi 57,3% uz fer verovatnoću iz kvota 49,2%, tu je glavna prednost; odigrani parovi 57,6% prema neodigranim 57,1%, najviše ponavljana četvrtina parova 52% prema 59,4% za ostale. "
   "(2) Stara Šansa (v5): AUC 0,547, isto kao same kvote 0,545, van uzorka 0,532; Vrednost AUC 0,50 (ne razlikuje). v6 sa kontekstom: rolling van uzorka (dani 4 do 8) najbolja četvrtina 54,7% → 65,4%, donja trećina 48,8% → 44,5%. "
   "(3) Korelacija minusa u istoj utakmici ≈ 0 (isti tim −0,002, protivnici +0,001, isti igrač dve statistike +0,10); tiketi oko jedne utakmice ne prolaze češće. "
   "(4) Minutaža: 12–17 min ponuda 55,9% (P 52%, S 67%, A 64%), 25+ min 63%; kod 12–17 min u 32% slučajeva igrač odigra 30%+ više minuta i tada minus prolazi 35%. "
   "(5) Dužina: 8@100 338 tiketa, 6 dobitnih, ROI +206% sa povraćajima; 10@50 124 tiketa, 1 dobitni; 12@50 36 tiketa bez dobitka; simulacija: pri prolazu 56% desetke imaju veći očekivani dobitak ali ređe dobitne dane, pri 53% i niže gube više; pri 50% gube sve kombinacije. Povraćaj za tiket od 50 din još nepoznat (čeka mvkrx2ug8ec7u). "
   "Promena: ★ bez dodatnih ponavljanja (g.v6, strong=false); Vrednost fokus označen kao nepreporučen. Sledeća provera posle 10. kola.")
if N not in notes: notes.append(N)
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open('test_review.html','w').write(h); print('ok')
