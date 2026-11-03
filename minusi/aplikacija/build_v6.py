import re,json,time,sys
src=sys.argv[1]; OUT=sys.argv[2]
h=open(src).read()
orig=open('app.orig.js').read(); new=open('app.js').read()
assert h.count(orig)==1
h=h.replace(orig,new)
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
st['ctx2']=json.load(open('ctx2.json'))
notes=st['notes']['text']
N1=("Kolo 7, 23.10.2026, rezultati upisani: 46 tiketa za 3.900 din iz dobitka. Dobitak: osmica mvkrx2ug5j4uw (kvota 183,06, 100 din) 18.306,42 + bonus 16% 2.929,03 = 21.235,45 din. "
    "Jedan promašaj (povraćaj čeka iznos): mvkrx2ugzvnty (Saben Lee A), mvkrx2ugjnjyb (Besson S), mvkrx2ug8ec7u (desetka, Shorts P). Parova 47, prošlo 31 (66%), po mestima na tiketima 64%. "
    "Glavni promašaji iz brzog meča Pariz – Valensija 93:104 (Brooks P 22, Shorts P 25) i Žalgiris – Asvel 105:85 (Butkevičius, Tubelis P 14, Crowder S 6, Saben Lee A 7). Dodatni tiket od 20 din sa plusevima izgubljen (nije upisan). minLog osvežen sa utakmicama 68 do 70.")
N2=("Generator v6 (24.10.2026): na v5 dodat kontekst utakmice (state.ctx2): pozicijska odbrana protivnika (G/F/C, za P/S/A, skupljeno n/(n+6)), očekivani poeni tima (kvote utakmica, bez njih proseci timova), tesan meč (razlika do 5), vruća forma (učinak po minutu u poslednje 3 iznad 130% sezone), rezervista autsajdera. "
    "z += −1,5·(odbrana−1) − 1,5·(ritam−1) + 0,2·tesan − 0,15·vruć − 0,1·rezervista autsajdera. Na 1.124 minusa iz cele ponude (8 dana) najbolja četvrtina: 62% → 69%, bolje u 6 od 8 dana; koeficijenti birani na istim podacima, pa pratiti. "
    "Posle svakog kola osvežiti ctx2 i minLog iz box score-a (skripte form/build.py, form/ctx2.py), a pre kola uneti kvote utakmica (team totals) jer one nose najveći deo efekta ritma.")
for n in (N1,N2):
    if n not in notes: notes.append(n)
st['savedAt']=int(time.time()*1000)
js=json.dumps(st,separators=(',',':')).replace('<','\\u003c')
h=pat.sub(lambda m:m.group(1)+js+m.group(3),h,count=1)
open(OUT,'w').write(h)
print('ok',len(h))
