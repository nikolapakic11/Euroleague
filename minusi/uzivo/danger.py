import json,re,collections
exec(open('/home/claude/live29/status.py').read().split("for g,i in GINFO.items()")[0])
R=[]
for t in T:
    S_=[st(l) for l in t['legs']]; R.append((t,S_,sum(1 for s in S_ if s[0]=='miss')))
alive=[(t,S_) for t,S_,m in R if m==0]
one=[(t,S_) for t,S_,m in R if m==1]
ca=collections.Counter(); c1=collections.Counter(); info={}
for t,S_ in alive:
    for l,s in zip(t['legs'],S_):
        if s[0] in('live','pend'): k=(l['p'],l['stat'],l['line']); ca[k]+=1; info[k]=s
for t,S_ in one:
    for l,s in zip(t['legs'],S_):
        if s[0] in('live','pend'): k=(l['p'],l['stat'],l['line']); c1[k]+=1; info[k]=s
def mins(x):
    if not x or ':' not in str(x): return 0
    a,b=str(x).split(':'); return int(a)+int(b)/60
out=[]
for k in set(ca)|set(c1):
    s=info[k]; e=S.get(k); b=s[2]
    em=re.search(r'\((\d+) min\)',e['role']) if e else None; em=int(em.group(1)) if em else 22
    m=mins(b['min']) if b else 0
    proj=s[1]*em/m if m>2 and s[1] is not None else None
    out.append((proj/k[2] if proj else 0,k,s[1],b['min'] if b else '-',em,proj,ca[k],c1[k]))
out.sort(key=lambda x:-x[0])
for r,k,v,mn,em,proj,a,o in out[:25]:
    print(f"{k[0]:20s} {k[1]}<{k[2]:5} sada {v} ({mn}), prosek min {em}, projekcija {proj and round(proj,1)} | zivih {a}, sa 1 promasajem {o}")
print('zivih',len(alive),collections.Counter((len(t['legs']),t['stake']) for t,_ in alive))
