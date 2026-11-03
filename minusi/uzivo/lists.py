import json,collections
exec(open('/home/claude/live29/status.py').read().split("for g,i in GINFO.items()")[0])
def finished_team(p):
    b=find(p); return b and finished(b['g'])
GM={'Real Madrid':83,'Fenerbahce':83,'Crvena Zvezda':81,'Bayern':81,'Maccabi Tel Aviv':82,'Paris':82}
def res(p,s,l,team,over=False):
    b=find(p); g=GM.get(team)
    if not b:
        return ('NIJE IGRAO',None) if g in GINFO and (finished(g) or GINFO[g]['q']>=3) else ('ČEKA',None)
    if b['min'] in ('DNP','',None,'00:00'): return ('NIJE IGRAO',None) if finished(b['g']) else ('ČEKA',None)
    v=b[s]; fin=finished(b['g'])
    if over:
        if v>l: return ('PROŠAO',v)
        return ('PAO',v) if fin else ('U TOKU',v)
    if v>l: return ('PAO',v)
    return ('PROŠAO',v) if fin else ('U TOKU',v)
M20=[('Theo Maledon','Real Madrid','A',5.5),('Shavon Shields','Fenerbahce','P',13.5),('Facundo Campazzo','Real Madrid','A',4.5),('Jordan Nwora','Crvena Zvezda','P',16.5),('Chima Moneke','Crvena Zvezda','S',4.5),('Will Clyburn','Fenerbahce','P',9.5),('Andres Feliz','Real Madrid','A',3.5),('Wade Baldwin','Fenerbahce','A',4.5),('Andreas Obst','Bayern','P',11.5),('Talen Horton-Tucker','Fenerbahce','S',3.5),('Walter Tavares','Real Madrid','P',9.5),('Nicolo Melli','Fenerbahce','S',4.5),('Jared Rhoden','Paris','A',2.5),('Semi Ojeleye','Crvena Zvezda','S',3.5),('Nadir Hifi','Paris','P',20.5),('Alize Johnson','Paris','S',4.5),('Austin Wiley','Bayern','P',6.5),('Duane Washington','Bayern','P',15.5),('Braxton Key','Fenerbahce','P',7.5),('Oshae Brissett','Maccabi Tel Aviv','S',4.5)]
P9=[('Justinian Jessup','Bayern','P',6.5),('Keaton Wallace','Maccabi Tel Aviv','P',5.5),('Vladimir Lucic','Bayern','S',2.5),('Ebuka Izundu','Crvena Zvezda','S',3.5),('Bonzie Colson','Maccabi Tel Aviv','P',9.5),('Tyson Carter','Crvena Zvezda','P',8.5),('Leopold Cavaliere','Paris','P',3.5),('Roman Sorkin','Maccabi Tel Aviv','P',11.5),('Rokas Jokubaitis','Bayern','P',8.5)]
out={}
def show(nm,L,over=False):
    c=collections.Counter(); rows=[]
    for p,t,s,l in L:
        r=res(p,s,l,t,over); c[r[0]]+=1; rows.append((p,s,l,r))
    print('==',nm,dict(c))
    for x in rows: print('  ',x)
show('20 MINUSA',M20); show('9 PLUSEVA',P9,True)
cnt=collections.Counter((l['p'],l['team'],l['stat'],l['line']) for t in T for l in t['legs'])
c=collections.Counter(); w=collections.Counter(); rows=[]
for k,n in cnt.items():
    r=res(k[0],k[2],k[3],k[1]); c[r[0]]+=1; w[r[0]]+=n; rows.append((n,k,r))
print('== PAROVI NA 40 TIKETA',dict(c),'po mestima',dict(w))
for x in sorted(rows,key=lambda x:(-x[0])): print('  ',x)
