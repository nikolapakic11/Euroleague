import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(viewport={'width':1200,'height':900})
        errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('file:///mnt/user-data/outputs/artifacts/4e6060cb-b4ba-489e-9b01-714a7c3468f9/index.html'); await pg.wait_for_timeout(1200)
        found=[]
        for tab in ('novi','tiketi','generator','analiza','rezultati'):
            el=await pg.query_selector(f'button[data-act="tab"][data-v="{tab}"]')
            if not el: continue
            await el.click(); await pg.wait_for_timeout(1000)
            t=await pg.evaluate("()=>document.body.innerText")
            if 'Kolo 9, 30.10' in t: found.append(tab)
        print('plan vidljiv u:',found,'ERR',errs)
        await b.close()
asyncio.run(main())
