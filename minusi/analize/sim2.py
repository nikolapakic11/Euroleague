exec(open('sim.py').read().split('import sys')[0])
for mu in (0.50,):
    print(f'=== prolaz parova {mu:.0%}')
    for nm in ('40 osmica po 100','80 osmica po 50','32x8 po 100 + 12x10 + 2x12 po 50','80 desetki po 50','40 sedmica po 100'):
        o=sim(CF[nm],mu,reps=1500); tot=o.sum(1)
        print(f'  {nm:34s} ocek. neto/dan {o.mean():+7.0f} | 20 dana u plusu {np.mean(tot>0):.2f} | medijana {np.median(tot):+8.0f} | najgorih 10% {np.percentile(tot,10):+8.0f}')
o=sim(CF['80 osmica po 50'],0.56,R50=278,reps=1500); print('80x8 po 50 ako povracaj isti kao za 100 din: ocek. neto/dan',round(o.mean()))
# how often a 12 wins
for n in (7,8,9,10,12):
    for p in (0.53,0.56,0.58): print(n,p,'1 dobitni na',round(1/p**n),'tiketa', end='; ')
    print()
