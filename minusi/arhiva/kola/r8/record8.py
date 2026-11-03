import re,json,time,collections
A=json.load(open('/mnt/user-data/outputs/plan_42_27okt.txt'))['tickets'][:5]
B=json.load(open('/mnt/user-data/outputs/plan_87_ostatak_27okt.txt'))['tickets'][:50]
C=json.load(open('/mnt/user-data/outputs/plan_37_ostatak_27okt.txt'))['tickets']
T=A+B+C
H='/mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'
h=open(H).read()
pat=re.compile(r'(<script type="application/json" id="state">)(.*?)(</script>)',re.S)
st=json.loads(pat.search(h).group(2))
ex=[t for t in st['tickets'] if t.get('date')=='2026-10-27']
print('vec upisano za 27.10:',len(ex))
new=[{'id':'r8d1-%02d'%(k+1),'date':'2026-10-27','round':'8','stake':t['stake'],'fund':'dobitak','legs':[{'p':l['p'],'team':l['t'],'stat':l['s'],'line':l['l'],'odds':l['u']} for l in t['legs']]} for k,t in enumerate(T)]
st['tickets']=[t for t in st['tickets'] if not t['id'].startswith('r8d1-')]+new
note=('Kolo 8, 27.10.2026: odigrano 92 tiketa za 6.085 din iz dobitka (upisao Claude iz planova, kvote iz ponude u trenutku pravljenja plana): 30 osmica po 100, jedna osmica od 35, 42 desetke i 19 dvanaestica po 50. '
      'Tok: 5 osmica iz jutarnjeg plana (Parra skinut iz ponude), 50 iz plana od 87 (Peters skinut iz ponude), 37 iz poslednjeg plana. Parra i Peters nisu računati kao odsutni (izveštaj ih ne pominje); Tyrese Martin van novih tiketa jer je kladionica podigla njegove granice. Peters je na 19 odigranih tiketa; ako ne zaigra, par se vraća.')
if note not in st['notes']['text']: st['notes']['text'].append(note)
st['savedAt']=int(time.time()*1000)
h=pat.sub(lambda m:m.group(1)+json.dumps(st,separators=(',',':')).replace('<','\\u003c')+m.group(3),h,count=1)
open(H,'w').write(h)
json.dump(new,open('/home/claude/r8/played92.json','w'),ensure_ascii=False)
print(len(new),sum(t['stake'] for t in new),collections.Counter((len(t['legs']),t['stake']) for t in new))
