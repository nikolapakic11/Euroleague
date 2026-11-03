import numpy as np
rng=np.random.default_rng(7)
BON={7:.11,8:.16,9:.21,10:.26,12:.36}
def sim(cfg,mu,R100=278,R50=139,days=20,reps=4000,npairs=40,O=1.89,dsd=0.03,psd=0.05):
    out=np.zeros((reps,days))
    for r in range(reps):
        for d in range(days):
            dm=mu+rng.normal(0,dsd); p=np.clip(dm+rng.normal(0,psd,npairs),0.3,0.85); hit=rng.random(npairs)<p
            net=0
            for n,cnt,stake in cfg:
                for _ in range(cnt):
                    idx=rng.choice(npairs,n,replace=False); m=n-hit[idx].sum()
                    net-=stake
                    if m==0: net+=stake*O**n*(1+BON[n])
                    elif m==1: net+=R100 if stake==100 else R50
            out[r,d]=net
    return out
CF={'40 osmica po 100':[(8,40,100)],
    '80 osmica po 50':[(8,80,50)],
    '32x8 po 100 + 12x10 + 2x12 po 50':[(8,32,100),(10,12,50),(12,2,50)],
    '20x8 po 100 + 40x10 po 50':[(8,20,100),(10,40,50)],
    '80 desetki po 50':[(10,80,50)],
    '40 sedmica po 100':[(7,40,100)]}
import sys
for mu in (0.53,0.56,0.58):
    print(f'=== prolaz parova {mu:.0%}, kvota 1,89, budzet oko 4.000 din dnevno, 20 dana')
    for nm,cfg in CF.items():
        o=sim(cfg,mu,reps=1500)
        tot=o.sum(1); budget=sum(c*s for n,c,s in cfg)
        print(f'  {nm:34s} ulog/dan {budget:5d} | ocek. neto/dan {o.mean():+7.0f} | dan u plusu {np.mean(o>0):.2f} | 20 dana u plusu {np.mean(tot>0):.2f} | 20 dana medijana {np.median(tot):+8.0f} | najgorih 10% {np.percentile(tot,10):+8.0f}')
