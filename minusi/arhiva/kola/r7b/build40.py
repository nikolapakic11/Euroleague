import json,re,math,random,collections,time
import numpy as np
from statistics import NormalDist
ND=NormalDist()
h=open('/mnt/user-data/outputs/evroliga-minusi.html').read()
st=json.loads(re.search(r'<script type="application/json" id="state">(.*?)</script>',h,re.S).group(1))
picks=st['offer']['picks']
best=json.load(open('best.json'))
SEL=[('Scottie Wilbekin','P'),('Ante Zizic','S'),('Dario Saric','P'),('Andreas Obst','P'),('Johannes Thiemann','S'),('Dwayne Bacon','A'),('Elie Okobo','P'),
('Theo Maledon','P'),('Facundo Campazzo','A'),('Walter Tavares','P'),('Jaylen Hoard','S'),('Kendrick Nunn','A'),('Leandro Bolmaro','A'),('Alec Peters','P'),
('Moses Wright','P'),('Joel Parra','A'),('Jordan Nwora','P'),('Chima Moneke','P'),('Nick Weiler Babb','A'),('Carlik Jones','P')]
import unicodedata
def na(x): x=unicodedata.normalize('NFD',x); return ''.join(c for c in x if unicodedata.category(c)!='Mn').lower().replace('-',' ').replace('.','')
GAME={'Anadolu Efes':'IST-BES','Besiktas':'IST-BES','Bayern':'MUN-DUB','Bayern Munich':'MUN-DUB','Dubai':'MUN-DUB','Maccabi Tel Aviv':'TEL-MAD','Real Madrid':'TEL-MAD','Panathinaikos':'PAN-BAS','Baskonia':'PAN-BAS','Olimpia Milano':'MIL-BAR','Barcelona':'MIL-BAR','Partizan':'PAR-RED','Crvena Zvezda':'PAR-RED','Crvena zvezda':'PAR-RED'}
SN={'P':'Poeni','S':'Skokovi','A':'Asistencije'}
P=[]
for name,s in SEL:
    pk=[p for p in picks if na(p['p'])==na(name) and p['s']==s]; assert len(pk)==1,(name,len(pk))
    pk=pk[0]
    b=[x for x in best if na(x['name'])==na(name)]; assert b and b[0]['s'].startswith(SN[s][:5]),(name,b[:1])
    fair=(1/pk['u'])/((1/pk['u'])+(1/pk['o'])) if pk.get('o') else 1/pk['u']/1.06
    P.append(dict(c=pk['c'],p=pk['p'],t=pk['t'],s=s,l=pk['l'],u=pk['u'],pr=b[0]['pr'],fair=fair,g=GAME[pk['t']],time=pk['time']))
n=len(P); assert n==20
for x in P: print(x['p'],x['t'],x['g'],x['s'],x['l'],x['u'],round(x['pr'],3),round(x['fair'],3),x['time'][-5:])
json.dump(P,open('sel20.json','w'),ensure_ascii=False)
