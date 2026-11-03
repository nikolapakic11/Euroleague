import json,numpy as np,collections
st=json.load(open('/home/claude/app/v6/state_now.json')); L=json.load(open('legs.json'))
res=st['results']
def key(t,l):
    ln=l['line']; ls=str(int(ln)) if float(ln).is_integer() else repr(float(ln))
    return '|'.join([str(t['round']).strip(),l['p'].strip().lower(),l['stat'],ls])
S=collections.defaultdict(lambda:collections.Counter())
for t in st['tickets']:
    n=len(t['legs']); od=1; miss=0; valid=0
    for l in t['legs']:
        r=res.get(key(t,l))
        if not r or r.get('dnp'): continue
        valid+=1
        if r['actual']<l['line']: od*=l['odds']
        else: miss+=1
    win=t['stake']*od if miss==0 else 0
    k=(n if n in (7,8,9,10,12) else 'ostalo', t['stake'] if t['stake'] in (50,100) else 'ostalo')
    c=S[k]; c['tiketa']+=1; c['ulog']+=t['stake']; c['dobitak']+=win+(t.get('bonus') or 0); c['povracaj']+=t.get('refund') or 0
    c['dobitnih']+=miss==0; c['jedan']+=miss==1 and valid>=7; c['povr_n']+=bool(t.get('refund'))
    c['parova']+=valid; c['proslo']+=valid-miss
for k in sorted(S,key=str):
    c=S[k]; print(k, dict(tiketa=c['tiketa'],ulog=c['ulog'],dobitnih=c['dobitnih'],dobitak=round(c['dobitak']),jedan_promasaj=c['jedan'],povracaja=c['povr_n'],povracaj=round(c['povracaj']),ROI=round((c['dobitak']+c['povracaj'])/c['ulog']-1,2),prolaz_parova=round(c['proslo']/c['parova'],3)))
print('prosecan povracaj', round(sum(t.get('refund') or 0 for t in st['tickets'])/sum(1 for t in st['tickets'] if t.get('refund')),1))
# winners list
for t in st['tickets']:
    if t.get('bonus'): print('dobitni',t['date'],t['stake'],len(t['legs']),t['bonus'])
