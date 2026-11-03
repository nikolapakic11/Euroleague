import re,json,time
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
cur=open('/home/claude/app/v6/app.js').read(); assert h.count(cur)==1
js=cur
def rep(old,new,cnt=1):
    global js
    assert js.count(old)==cnt,(js.count(old),old[:60]); js=js.replace(old,new)
rep("    if (!g.v6) { g.v6 = true; g.strong = false; }","    if (!g.v6) { g.v6 = true; g.strong = false; }\n    // od 28.10.2026: najmanja kvota 1,65 (Nikola), parovi ispod 1,70 raspoređeni najviše po jedan na tiketu\n    if (!g.v7) { g.v7 = true; if (!g.minOdds || g.minOdds === '1.70') g.minOdds = '1.65'; }")
rep("minOdds: '1.70'","minOdds: '1.65'",3)
open('/home/claude/app/v6/app.v7.js','w').write(js)
h=h.replace(cur,js)
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
REF={'r5d1-05':100,'r5d1-13':300,'r5d1-32':200,'r5d1-26':300,'r5d1-09':300,'r7d1-8-18':100,'r7d1-8x-05':300,'r8d1-16':100,'r8d1-05':200,'r8d1-25':300,'r8d1-29':500}
for t in st['tickets']:
    if t['id'] in REF: t['refund']=REF[t['id']]
for n in ("AdmiralBet povraćaj (utvrđeno 28.10.2026. na svim povraćajima do sada): kad tiket padne na tačno jednom paru (bar 7 važećih parova), vraća se ulog puta množilac koji zavisi od kvote ostalih (prošlih) parova: ispod 50 x1, od 50 do 70 x2, od 70 do oko 95 x3, od oko 99 naviše x5 (najveće viđeno 274, i dalje x5). Važi i za tikete od 50 din. Pojedinačni iznosi za 13.10, 22.10. i 27.10. preračunati po tom pravilu i slažu se sa ukupnim iznosima.",
          "Od 28.10.2026. najmanja kvota je 1,65 (Nikola); parove sa kvotom od 1,65 do 1,69 rasporediti, najviše jedan po tiketu.",
          "28.10.2026: Nikola uplatio 2.900 din svežeg novca; sa 1.100 od povraćaja ukupno 4.000 din za 40 osmica po 100."):
    if n not in st['notes']['text']: st['notes']['text'].append(n)
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h); print('ok')
