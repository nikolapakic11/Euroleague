import asyncio,sys,json
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1400,'height':1000})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file:///home/claude/r8/'+sys.argv[1]); await pg.wait_for_timeout(1200)
        await pg.click('button[data-act="tab"][data-v="generator"]'); await pg.wait_for_timeout(2000)
        for k in (sys.argv[3].split(',') if len(sys.argv)>3 and sys.argv[3] else []):
            el=await pg.query_selector(f'input[data-abs="{k}"]')
            if el and await el.is_checked(): await el.click(); await pg.wait_for_timeout(1500)
        for nm in (sys.argv[4].split(',') if len(sys.argv)>4 and sys.argv[4] else []):
            await pg.fill('#absAdd', nm); await pg.click('button[data-act="absAdd"]'); await pg.wait_for_timeout(1500)
        data=await pg.evaluate("""()=>{
          const out={abs:[],pool:[]};
          document.querySelectorAll('table[data-sid="gen-abs"] tbody tr').forEach(r=>{const c=r.querySelectorAll('td');out.abs.push({on:c[0].querySelector('input').checked,name:c[1].innerText,team:c[2].innerText,pos:c[3].innerText,min:c[4].innerText,why:c[5].innerText})});
          document.querySelectorAll('input[data-gx]').forEach(inp=>{const r=inp.closest('tr');const c=r.querySelectorAll('td');
            out.pool.push({k:inp.dataset.gx,on:inp.checked,dim:r.style.opacity==='0.5',p:c[2].innerText.split('\\n')[0].replace('★ ',''),star:c[2].innerText.startsWith('★'),t:c[3].innerText.split('\\n')[0],opp:c[4].innerText.split('\\n')[0],s:c[5].innerText.split('\\n')[0],l:+c[6].dataset.v,u:+c[7].dataset.v,cur:c[8].innerText.replace(/\\n/g,' '),exp:c[10].dataset.v,pr:+c[12].dataset.v,ev:+c[13].dataset.v,role:c[14].innerText.replace(/\\n/g,' | ')});});
          return out;}""")
        json.dump(data,open(sys.argv[2],'w'),ensure_ascii=False)
        print('abs',len(data['abs']),'pool',len(data['pool']),'ERR',errs)
        await b.close()
asyncio.run(main())
